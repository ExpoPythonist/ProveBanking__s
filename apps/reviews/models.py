from datetime import timedelta

from django.db import models, connection
from django.db.models import Sum, Avg
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models.signals import post_init, post_save
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django_extensions.db.fields import UUIDField
from django.utils.timezone import now

from filtered_contenttypes.fields import FilteredGenericForeignKey

from vlkjsonfield.fields import VLKJSONField
from autoslug.fields import AutoSlugField
from model_utils.managers import QueryManager

from med_social.utils import humanized_datetime, send_notification_mail
from med_social.utils import get_score_level
from med_social.tasks import send_all_notification_task
from notifications.signals import notify

from .fields import base as metric_fields


def _get_default_metric_data():
    return metric_fields.BaseField.get_metric_data()


class Metric(models.Model):
    '''Facilitates custom metrics for reviews. Each metric can contain a
    score of 1-5 and have custom labels'''
    _supported_models = set([])

    SOURCE_AUTO = 1
    SOURCE_IMPORT = 2
    SOURCE_CLIENT = 3
    SOURCE_VENDOR = 4

    SOURCE_CHOICES = (
        (SOURCE_AUTO, 'Calculated by Proven',),
        # (SOURCE_IMPORT, 'Imported from another data source',),
        (SOURCE_CLIENT, 'Manually entered by client',),
        (SOURCE_VENDOR, 'Manually entered by vendor',),
    )
    DEFAULT_FIELD_CLASS = metric_fields.RatingField

    FIELD_CLASSES = {F.ID: F for F in metric_fields.FIELDS}
    FIELD_KIND_CHOICES = tuple([(F.ID, F.name,) for F in metric_fields.FIELDS])

    PERMISSIONS = (
        ('add_metric', 'Can add metric', Permission.CLIENT, True),
        ('view_metric', 'Can view metric', Permission.CLIENT, False)
    )

    name = models.CharField(_('metric name'), max_length=127)
    slug = AutoSlugField(populate_from='name', unique_with=['content_type'])
    help_text = models.TextField(_('help text'), default='', blank=True)
    weight = models.PositiveSmallIntegerField(default=0)
    kind = models.CharField(
        max_length=127,
        default=metric_fields.RatingField.ID, choices=FIELD_KIND_CHOICES)
    metric_data = VLKJSONField(
        default=_get_default_metric_data)
    source = models.PositiveSmallIntegerField(default=SOURCE_CLIENT,
                                              choices=SOURCE_CHOICES)
    is_deleted = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, related_name='metrics')

    objects = QueryManager(is_deleted=False)
    deleted_objects = QueryManager(is_deleted=True)
    all_objects = models.Manager()

    class Meta:
        ordering = ('-weight', 'id',)
        unique_together = (('content_type', 'slug',),)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id and not self.weight:
            weight = 100.0 - (Metric.objects.all().aggregate(
                Sum('weight')).get('weight__sum') or 0)
            if weight >= 0:
                self.weight = weight
        return super(Metric, self).save(*args, **kwargs)

    @classmethod
    def is_weight_sum_ok(klass, content_type):
        """ Tests if the given set of metrics has weight == 100 """
        queryset = Metric.objects.filter(content_type=content_type).all()
        return queryset.aggregate(Sum('weight')).get('weight__sum') == 100

    @property
    def is_enabled(self):
        return not(self.is_deleted and self.weight == 0)

    @property
    def field(self):
        if not hasattr(self, '__field__'):
            self.__field__ = self.FIELD_CLASSES[self.kind](self)
        return self.__field__

    @property
    def as_field_name(self):
        return self.name.lower().replace(' ', '')

    @classmethod
    def get_supported_models(self):
        return self._supported_models

    def get_display_choices(self):
        choices = [self.field.as_form_choice(label)
                   for label in self.metric_data['labels'].items()]
        return sorted(choices)

    def get_score_display(self, score):
        return self.field.get_score_display(score)

    def set_labels_from_kind(self):
        self.labels = self.field.labels

    def calculate_auto_score(self, value):
        return self.field.calculate_auto_score(value, self.metric_data['labels'])

    def clean(self):
        if not self.content_type_id:
            # If content-type has not been attached yet, skip the cleaning
            # it will be attched in future for sure as it is required
            return

        claimed = self.__class__.objects.filter(
            content_type=self.content_type
        ).exclude(id=self.id).aggregate(
            models.Sum('weight'))['weight__sum'] or 0

        available = 100 - claimed
        if self.weight and self.weight > available:
            raise ValidationError('Weight cannot be more than {}% as other'
                                  ' metrics collectively weigh {}%.'
                                  .format(available, claimed))

    def clean_metrics(self):
        if self.field:
            labels = self.metric_data.get('labels', {})
            for K, V in labels.items():
                labels[K] = self.field.clean(V)
            self.metric_data['labels'] = labels


class Review(models.Model):
    '''Review of a vendor by a client resource'''

    PERMISSIONS = (
        ('add_review', 'Can add review', Permission.CLIENT, False),
        ('view_review', 'Can view review', Permission.ALL, False)
    )
    content_type = models.ForeignKey(ContentType, related_name='reviews')
    object_id = models.PositiveIntegerField()
    content_object = FilteredGenericForeignKey('content_type', 'object_id')

    metrics = models.ManyToManyField(Metric, through='MetricReview')
    remarks = models.TextField(_('remarks'), default='', blank=True)
    score = models.DecimalField(blank=True, null=True, max_digits=2,
                                decimal_places=1)
    posted_by = models.ForeignKey('users.User', related_name='reviews_submitted',
                                  null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    anonymous = models.BooleanField(default=False)
    vendor_viewable = models.BooleanField(default=False)

    token = models.ForeignKey('ReviewToken', related_name='review',
                              null=True, blank=True)

    class Meta:
        get_latest_by = 'created'
        ordering = ('-created',)

    def __unicode__(self):
        if len(self.remarks) > 30:
            return '"{}..."'.format(self.remarks[:30].capitalize())
        return '"{}"'.format(self.remarks.capitalize())

    def save(self, *args, **kwargs):
        self.score = self.calculate_score()
        ret_val = super(Review, self).save(*args, **kwargs)
        if self.content_object:
            self.content_object.__Reviews__denorm_reviews__()
        return ret_val

    def delete(self, *args, **kwargs):
        content_object = self.content_object
        super(Review, self).delete(*args, **kwargs)
        if content_object:
            content_object.__Reviews__denorm_reviews__()

    def natural_created_date(self):
        return humanized_datetime(self.created)

    def calculate_score(self):
        score_sum = 0.0
        weight_sum = 0.0
        count = 0
        for metricreview in self.review_metrics.all():
            count += 1
            weight = metricreview.metric.weight
            score = float(metricreview.score)
            score_sum += (score * weight)
            weight_sum += weight
        if not score_sum or not weight_sum:
            return None
        return float('{:.1f}'.format(score_sum / weight_sum))

    def get_score_level(self):
        return get_score_level(self.score)

    def get_score_color(self):
        if not self.score:
            return '#D7D7D7'
        if self.score <= 2:
            return '#FF5600'
        elif self.score <= 3.5:
            return '#FFAD82'
        elif self.score <= 4:
            return '#80EE49'
        elif self.score <= 5:
            return '#3DBA3F'

    def get_notification_receivers(self):
        if hasattr(self.content_object, 'get_notification_receivers'):
            return self.content_object.get_notification_receivers()
        else:
            return []

    def get_absolute_url(self):
        return reverse('reviews:detail', args=(self.id,))

    def score_update(self):
        from vendors.models import Score
        score_obj, _ = Score.objects.get_or_create(vendor=self.content_object,
                                                   kind=Score.KIND_REVIEW)
        reviews = Review.objects\
            .filter(content_object=self.content_object)
        review_score = reviews.aggregate(Avg('score'))['score__avg']
        review_count = reviews.count()
        if not review_score:
            review_score = 0
        score = review_score + (review_score * review_count)
        if score:
            score_obj.score = score
        self.content_object.save()
        score_obj.save()


class MetricReview(models.Model):
    '''Through table for Metric-Review relationship. Also stores score given
    to the particular metric'''
    SCORE_1 = 1
    SCORE_2 = 2
    SCORE_3 = 3
    SCORE_4 = 4
    SCORE_5 = 5
    SCORE_CHOICES = (
        (SCORE_1, '1',),
        (SCORE_2, '2',),
        (SCORE_3, '3',),
        (SCORE_4, '4',),
        (SCORE_5, '5',),
    )
    review = models.ForeignKey(Review, related_name='review_metrics')
    metric = models.ForeignKey(Metric, related_name='review_metrics')
    score = models.DecimalField(max_digits=2, decimal_places=1)

    def get_metric_score_display(self):
        return self.metric.get_score_display(str(self.score))


class ReviewToken(models.Model):
    uuid = UUIDField(auto=True)

    content_type = models.ForeignKey(ContentType, related_name='review_token')
    object_id = models.PositiveIntegerField()
    content_object = FilteredGenericForeignKey('content_type', 'object_id')

    email = models.EmailField(_('email address'), max_length=254,)
    created = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    created_by = models.ForeignKey('users.User', null=True, blank=True)

    def is_expired(self):
        date_now = now() - timedelta(days=7)
        if date_now > self.created:
            return True
        return False

    def get_create_review_url(self):
        return reverse('reviews:public_review', args=(self.uuid,))
