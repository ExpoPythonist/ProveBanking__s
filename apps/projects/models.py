from __future__ import division
import os
import datetime

from django.conf import settings
from django.utils.html import mark_safe
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.db import connection, models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now, utc
#from django.contrib.contenttypes.fields import GenericRelation
from aggregate_if import Sum

from annoying.functions import get_object_or_None
from autoslug import AutoSlugField
from django_hstore import hstore
from shortuuid import uuid
from model_utils import FieldTracker
from model_utils.managers import QueryManager
from notifications.signals import notify
from rest_framework.renderers import JSONRenderer
from taggit.managers import TaggableManager

from med_social.utils import slugify
from med_social.libs.mixins import SerializableMixin
from med_social.utils import (humanized_date, humanized_datetime,
                              send_notification_mail, today,
                              days_in_date_range)
from categories.models import Category
from vendors.models import Vendor
from rates.models import Rate, MockRate
from reviews.models import Review
from reviews.db.fields import ReviewsField
from channels.models import Channel, Message
from activity.models import Event
from metrics.models import Metric
from .mixins import StatusModel


def urgency(date):
    date = datetime.date(date.year, date.month, date.day)
    diff = date - today()
    if diff.days <= 7:
        return 'danger'
    elif diff.days <= 14:
        return 'warning'
    return 'default'


class DurationMixin(object):
    @property
    def duration(self):
        return self.end_date - self.start_date

    def clean_fields(self, exclude):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError({'end_date': [
                    ('Oops! Looks like end date is before start date')]})


class Project(StatusModel, SerializableMixin):
    PERMISSIONS = (
        ('add_project', 'Can add project', Permission.CLIENT, False),
        ('view_project', 'Can view project', Permission.ALL, False)
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    user = models.ForeignKey('users.User', related_name='projects')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    ended = models.DateTimeField(blank=True, null=True)
    staff = models.ManyToManyField('users.User',
                                   related_name='assigned_projects',
                                   through='ProposedResource',
                                   through_fields=('project', 'resource'))
    budget = models.PositiveIntegerField(null=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    division = models.ForeignKey('divisions.Division', related_name='projects')

    owners = models.ManyToManyField('users.User',
                                    related_name='owned_projects',
                                    blank=True)
    last_activity = models.ForeignKey('users.User',
                                      related_name='modified_projects',
                                      null=True, blank=True)
    tags = TaggableManager(blank=True)
    tracker = FieldTracker(fields=['start_date', 'end_date'])

    class Meta:
        verbose_name = 'project'
        verbose_name_plural = 'projects'
        db_table = 'projects'
        ordering = ('status', '-modified')

    def __unicode__(self):
        return self.title

    @classmethod
    def can_create(self, user):
        return user.has_perm('projects.add_project')

    def clean(self):
        super(Project, self).clean()
        self.description = self.description.strip()
        self.title = self.title.strip()

    def clean_fields(self, exclude):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError({'end_date': [
                    ('Oops! Looks like end date is before start date')]})

    def get_absolute_url(self):
        return reverse('projects:detail', args=(self.id,))

    def get_edit_url(self):
        return reverse('projects:edit', args=(self.id,))

    @property
    def urgency(self):
        return urgency(self.end_date)

    @property
    def sorted_proposals(self):
        return self.proposals.order_by('resource__first_name')

    def fullfilled_requests_count(self):
        return self.staffing_requests\
            .filter(kind=StaffingRequest.KIND_STAFFING)\
            .filter(status=StaffingRequest.STAFFED).count()

    def update_status(self, commit=False):
        status_list = self.staffing_requests.values_list('status', flat=True)
        has_staffing = False
        has_draft = False
        has_staffed = False
        for S in status_list:
            if S == self.DRAFT:
                has_draft = True
            elif S == self.STAFFING:
                has_staffing = True
            elif S == self.STAFFED:
                has_staffed = True
        if has_staffing:
            self.status = self.STAFFING
        elif has_staffed and not has_draft:
            self.status = self.STAFFED
        elif has_draft and not has_staffed:
            self.status = self.DRAFT
        if commit:
            self.save(update_fields=('status', 'modified'))

    @property
    def budget_overun_close(self):
        tc = self.total_expected_cost
        if tc > self.budget:
            return False

        percent_left = 100 * (tc - self.budget) / self.budget
        if -20 <= percent_left <= 0:
            return True

        return False

    @property
    def natural_created_date(self):
        return humanized_datetime(self.created)

    @property
    def total_expected_cost(self):
        cost = 0
        # Cost from Deliverables
        cost += StaffingResponse.objects.filter(
            request__project=self, request__kind=StaffingRequest.KIND_FIXED,
            is_accepted=True
        ).aggregate(Sum('rate'))['rate__sum'] or 0

        # Cost from staff
        cost += self.proposals.filter(
            status__value=ProposedResourceStatus.SUCCESS
        ).aggregate(Sum('final_rate'))['final_rate__sum'] or 0
        return int(cost)

    def get_staff_providers(self):
        vendors = {}
        vendor_list = self.staff.values_list('vendor',
                                             'vendor__name').distinct('vendor')
        for vendor in vendor_list:
            vendor_details = vendors.get(vendor[0], {'name': vendor[1],
                                                     'count': 0})
            vendor_details['count'] += vendor_details['count'] + 1
            vendors[vendor[0]] = vendor_details
        return vendors

    def get_project_status(self):
        _today = today()
        if self.staffing_requests.filter(start_date__lte=_today,
                                         end_date__gte=_today).exists():
            return ('ongoing', _('Ongoing'),)
        elif self.staffing_requests.filter(end_date__lte=_today).exists():
            return ('finished', _('Finished'),)
        elif self.staffing_requests.filter(start_date__gte=_today).exists():
            return ('not-started', _('Not started'))

    def get_meta_counts(self):
        counts = {}
        counts['attachments'] = self.staffing_requests.filter(
            document__isnull=False).count()

        #counts['staff_proposed'] = self.proposals.count()
        num_resources = self.staffing_requests.filter(
            kind=StaffingRequest.KIND_STAFFING
        ).aggregate(
            count=Sum('num_resources')
        )
        counts['resources_requested'] = num_resources['count'] or 0
        counts['staff_accepted'] = self.proposals.filter(
            status__value=ProposedResourceStatus.SUCCESS
        ).count()

        counts['any'] = any(counts.values())
        return counts

    def post_event_object_delete(self, user):
        pass

    def create_event_object(self, user):
        content_type = ContentType.objects.get_for_model(Project)
        Event.objects.get_or_create(user=user,
                                    content_type_id=content_type.id,
                                    object_id=self.id,)


def _get_document_upload_path(instance, filename):
    tenant = connection.tenant
    t = "{0}/p/r/{1}/".format(tenant.id, instance.id)
    fn, ext = os.path.splitext(filename)
    fname = "{0}.{1}".format(uuid(), ext)
    return os.path.join(settings.PROTECTED_ROOT, t, 'docs', fname)


class StaffingRequest(StatusModel, SerializableMixin, DurationMixin):
    PROJECT_FIELDS = ('start_date', 'end_date')
    PERMISSIONS = tuple()

    KIND_STAFFING = 1
    KIND_FIXED = 2

    PROJECT_CHOICES = (
        (KIND_STAFFING, 'Staffing request',),
        (KIND_FIXED, 'Fixed price projects',),
    )

    KIND_NAMES = {
        KIND_STAFFING: 'staffing',
        KIND_FIXED: 'fixed',
    }

    KIND_NAMES_REVERSE = {V:K for K, V in KIND_NAMES.items()}

    FIXED = 1
    HOUR = 2
    DAY = 3

    WEEK = 4
    PERIOD_CHOICES = (
        (FIXED, 'Fixed',),
        (HOUR, 'Hourly',),
        (DAY, 'Daily',),
        (WEEK, 'Weekly',),
    )

    EDIT_CREATE = 1
    EDIT_PEOPLE = 2
    EDIT_VENDORS = 3
    EDIT_ADVANCED = 4

    channels_extra_help_text = ('These vendors will be given access to the '
                                'staffing request as well.')

    title = models.CharField(default='', blank=True, max_length=127)
                             #help_text='optional title for the request')
    kind = models.PositiveSmallIntegerField(default=KIND_STAFFING,
                                            choices=PROJECT_CHOICES)
    min_rate = models.DecimalField(null=True, blank=True,
                                   decimal_places=0, max_digits=10)
    max_rate = models.DecimalField(null=True, blank=True,
                                   decimal_places=0, max_digits=10)
    billing_period = models.PositiveSmallIntegerField(choices=PERIOD_CHOICES,
                                                      default=HOUR)

    description = models.TextField(_('Description'), blank=True)

    project = models.ForeignKey(Project, related_name='staffing_requests')
    categories = models.ManyToManyField(Category,
                                        related_name='staffing_requests')
    num_resources = models.PositiveSmallIntegerField(
        _('Number of people required'), default=1)
    allocation = models.PositiveSmallIntegerField(
        _('Allocation (%)'), default=100)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)

    created_by = models.ForeignKey('users.User',
                                   related_name='staffing_requests')
    last_activity = models.ForeignKey('users.User',
                                      related_name='staffing_activity',
                                      null=True, blank=True)
    is_public = models.BooleanField(default=False)
    vendors = models.ManyToManyField(
        Vendor,
        through='RequestVendorRelationship'
    )
    people = models.ManyToManyField(
        'users.User', related_name='visible_staffing_requests')
    proposed_staff = models.ManyToManyField(
        'users.User', related_name='proposed_staffing_requests')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    location = models.ForeignKey('locations.Location',
                                 related_name='staffing_requests',
                                 null=True, blank=True)
    skill_level = models.ForeignKey('categories.SkillLevel',
                                    null=True)
    role = models.ForeignKey('roles.Role', null=True,
                             related_name='staffing_requests')
    document = models.FileField(null=True, upload_to=_get_document_upload_path)

    owners = models.ManyToManyField('users.User',
                                    related_name='owned_requests',
                                    blank=True)

    meta = hstore.DictionaryField(default={})

    channels = GenericRelation(Channel)
    tracker = FieldTracker(fields=['start_date', 'end_date'])

    class Meta:
        ordering = ('-modified',)

    def __unicode__(self):
        return self.text_title

    def as_json(self):
        from API.serializers.request_serializers import LeanRequestSerializer
        return JSONRenderer().render(LeanRequestSerializer(self).data)

    def get_empty_positions(self):
        filled_positions = self.proposed.filter(
            status__value=ProposedResourceStatus.SUCCESS).count()
        p = self.num_resources - filled_positions
        return 0 if p < 0 else p

    def get_channel_vendor_choices(self, user):
        if user.is_client:
            return Vendor.objects.values_list('id', 'name')
        else:
            vendor = user.vendor
            return ((vendor.id, vendor.name,),)

    def get_channel_notification_users(self, channel):
        """Should return a queryset or a list.
        Users returned will be notified when a channel has a new message"""
        return self.owners.values_list('id', flat=True)

    def post_channel_create(self, channel):
        self.vendors.add(*channel.vendors.all())
        self.update_status(commit=True)

    def post_event_object_delete(self, user):
        content_project = ContentType.objects.get_for_model(Project)
        content_staffing = ContentType.objects.get_for_model(StaffingRequest)
        project_event = get_object_or_None(Event,
                                           user=user,
                                           content_type_id=content_project.id,
                                           object_id=self.project.id)
        if project_event:
            project = project_event.content_object
            staffing_list = list(project.staffing_requests.
                                 values_list('id', flat=True))
            if self.id in staffing_list:
                staffing_list.remove(self.id)

            staffing_list_events = Event.objects\
                .filter(user=user,
                        content_type_id=content_staffing.id,
                        object_id__in=staffing_list)

            if not staffing_list_events:
                project_event.delete()

    def create_event_object(self, user):
        content_type = ContentType.objects.get_for_model(StaffingRequest)
        Event.objects.get_or_create(user=user,
                                    content_type_id=content_type.id,
                                    object_id=self.id,)
        self.project.create_event_object(user=user)

    @property
    def natural_start_date(self):
        return humanized_date(self.start_date)

    @property
    def natural_end_date(self):
        return humanized_date(self.end_date)

    def get_start_date_display(self):
        return self.natural_start_date

    def get_end_date_display(self):
        return self.natural_end_date

    @property
    def natural_created_date(self):
        return humanized_datetime(self.created)

    @property
    def natural_fullfilled_date(self):
        return humanized_datetime(self.fullfilled)

    @property
    def is_staffing(self):
        return self.kind == self.KIND_STAFFING

    @property
    def is_fixed_price(self):
        return self.kind == self.KIND_FIXED

    @property
    def staffed_count(self):
        return self.proposed.filter(
            status__value=ProposedResourceStatus.SUCCESS).count()

    @property
    def accepted_vendors_count(self):
        return self.request_vendors.filter(
            answer=RequestVendorRelationship.accepted).count()

    @property
    def html_title(self):
        title = ''
        if self.title:
            group = self.title.split('(')
            title = group[0]
            if len(group) > 1:
                title += '&nbsp;<small>({})</small>'.format(''.join(group[1:]))
        if not title:
            title = '{}'.format(self.role)
            if self.skill_level:
                title += '&nbsp;<small>({})</small>'.format(self.skill_level)
        return mark_safe(title)

    @property
    def text_title(self):
        if self.title:
            return self.title
        elif self.role:
            title = '{}'.format(self.role)
            if self.skill_level:
                title += ' ({})'.format(self.skill_level)
        elif self.skill_level:
            title = self.skill_level
        else:
            title = 'Staffing request'
        return mark_safe(title)

    @property
    def urgency(self):
        return urgency(self.end_date)

    def get_or_create_response(self, user, vendor):
        responses = self.responses.filter(
            vendor=vendor, status=StaffingResponse.STATUS_SENT)
        if responses.exists():
            return responses.first()
        else:
            return self.responses.get_or_create(
                vendor=vendor, status=StaffingResponse.STATUS_SENT,
                defaults={'posted_by': user}
            )[0]

    def update_status(self, commit=False):
        old_status = self.status
        if self.kind == self.KIND_FIXED:
            if self.responses.filter(is_accepted=True).exists():
                self.status = self.STAFFED
            else:
                self.status = self.STAFFING
        elif self.kind == self.KIND_STAFFING:
            if self.proposed.filter(
                status__value=ProposedResourceStatus.SUCCESS
            ).count() >= self.num_resources:
                self.status = self.STAFFED
            else:
                self.status = self.STAFFING
        if self.status != old_status:
            self.modified = now()
        if commit:
            self.save(update_fields=('status', 'modified',))

    def get_kind_name(self):
        return self.KIND_NAMES[self.kind]

    def get_absolute_url(self):
        return reverse('staffing:requests:detail', args=(self.id,))

    def get_edit_url(self):
        return reverse('staffing:requests:edit', args=(self.id,))

    def clean_fields(self, exclude=None):
        exclude = exclude or []
        super(StaffingRequest, self).clean_fields(exclude)
        DurationMixin.clean_fields(self, exclude)
        if self.min_rate and self.max_rate:
            if self.min_rate >= self.max_rate:
                raise ValidationError(
                    {'min_rate': ['Min rate must be lesson than max rate']})


class RequestVendorRelationship(models.Model):
    accepted = 1
    rejected = 2
    answer_choices = (
        (accepted, 'accepted',),
        (rejected, 'rejected',),
    )

    ANSWER_LABELS = {
        accepted: 'Yes, I\'m on it',
        rejected: 'No, I will pass',
    }

    CSS_CLASSES = {
        rejected: 'warning',
        accepted: 'success',
    }

    request = models.ForeignKey(StaffingRequest,
                                related_name='request_vendors')
    vendor = models.ForeignKey('vendors.Vendor',
                               related_name='request_vendors')

    answer = models.PositiveSmallIntegerField(choices=answer_choices,
                                              null=True, blank=True,
                                              default=None)
    answered_at = models.DateTimeField(null=True, blank=True)
    answered_by = models.ForeignKey('users.User',
                                    related_name='request_vendor_answer',
                                    null=True, blank=True,)

    viewed_at = models.DateTimeField(null=True, blank=True)
    viewed_by = models.ForeignKey('users.User',
                                  related_name='request_vendor_view',
                                  null=True, blank=True,)

    comment = models.CharField(max_length=127, blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('users.User',
                                   related_name='request_vendors')

    metric = GenericRelation(Metric)

    tracker = FieldTracker(fields=['answer', 'comment'])

    class Meta:
        unique_together = (('request', 'vendor',),)

    def save(self, *args, **kwargs):
        if self.tracker.has_changed('answer'):
            self.answered_at = now()
        return super(RequestVendorRelationship, self).save(*args, **kwargs)

    @property
    def natural_created_date(self):
        return humanized_datetime(self.created)

    @property
    def natural_answered_date(self):
        return humanized_datetime(self.answered_at)

    @property
    def is_accepted(self):
        return self.answer == self.accepted

    def get_response_time(self):
        created_delta = now() - self.created
        if self.answered_at:
            return self.answered_at - self.created
        elif created_delta > datetime.timedelta(days=4):
            return created_delta
        return None


class StaffingResponse(models.Model, SerializableMixin, DurationMixin):
    PROJECT_FIELDS = ('start_date', 'end_data',)
    PERMISSIONS = (
        ('add_staffingresponse', 'Can add staffing response',
         Permission.ALL, False),
    )

    STATUS_DRAFT = 1
    STATUS_SENT = 2
    STATUS_CHOICES = (
        (STATUS_DRAFT, 'draft'),
        (STATUS_SENT, 'sent'),
    )

    rate = models.DecimalField(null=True, blank=True,
                               decimal_places=0, max_digits=10)
    billing_period = models.PositiveSmallIntegerField(
        choices=StaffingRequest.PERIOD_CHOICES, default=StaffingRequest.HOUR)

    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)

    request = models.ForeignKey(StaffingRequest, related_name='responses')
    vendor = models.ForeignKey(Vendor, related_name='responses', null=True)
    status = models.PositiveSmallIntegerField(choices=STATUS_CHOICES,
                                              default=STATUS_SENT)
    posted_by = models.ForeignKey('users.User',
                                  related_name='posted_responses')
    allocation = models.PositiveSmallIntegerField(
        _('Allocation (%)'), default=100)
    location = models.ForeignKey('locations.Location', null=True)
    role = models.ForeignKey('roles.Role', null=True,
                             related_name='staffing_responses')

    # Reccords who accepted a fixed price project
    is_accepted = models.BooleanField(default=False)
    accepted_by = models.ForeignKey('users.User',
                                    related_name='accepted_responses',
                                    blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    tracker = FieldTracker()

    objects = models.Manager()
    sent_responses = QueryManager(status=STATUS_SENT)
    received_responses = QueryManager(status=STATUS_SENT)
    drafts = QueryManager(status=STATUS_DRAFT)

    def __unicode__(self):
        if self.id and self.request:
            ret = '{}'.format(self.request)
        else:
            ret = 'staffing response'
        return ret

    def __init__(self, *args, **kwargs):
        super(StaffingResponse, self).__init__(*args, **kwargs)
        for field in self.PROJECT_FIELDS:
            setattr(self, 'is_contradicting_{}'.format(field),
                    lambda F=field: self.is_contradicting_field(F))

    def save(self, *args, **kwargs):
        if self.accepted_by:
            self.is_accepted = True
        ret = super(StaffingResponse, self).save(*args, **kwargs)
        if self.created and not self.response_time:
            # FIXME: Don't use request.created. Instead use the date each
            # vendor was invited to the request or the request was made pubic
            self.response_time = self.created - self.request.created
            return self.save()
        return ret

    def clean_fields(self, exclude=None):
        exclude = exclude or []
        super(StaffingResponse, self).clean_fields(exclude)
        DurationMixin.clean_fields(self, exclude)
        if self.rate and self.rate < 0:
            raise ValidationError('Rate cannot be negative')

    @property
    def staffed(self):
        return ProposedResource.objects.filter(
            response=self,
            status__value=ProposedResourceStatus.SUCCESS
        ).all()

    @property
    def num_days(self):
        return days_in_date_range(self.start_date, self.end_date)

    def total_cost(self):
        return self.rate

    @property
    def total_proposed_cost(self):
        if self.request.is_fixed_price:
            return self.rate
        staffed = self.proposed.filter()
        if staffed.exists():
            cost = 0
            for staff in staffed.all():
                cost += staff.total_cost()
            return cost
        return None

    @property
    def is_draft(self):
        return self.status == self.STATUS_DRAFT

    @property
    def is_sent(self):
        return not self.is_draft

    def mark_sent(self):
        self.status = self.STATUS_SENT

    @property
    def accepted(self):
        return self.is_accepted

    @property
    def natural_created_date(self):
        return humanized_datetime(self.created)

    @property
    def natural_modified_date(self):
        return humanized_datetime(self.modified)

    @property
    def natural_start_date(self):
        return humanized_date(self.start_date)

    @property
    def natural_end_date(self):
        return humanized_date(self.end_date)

    def get_start_date_display(self):
        return self.natural_start_date

    def get_end_date_display(self):
        return self.natural_end_date

    def get_allocation_display(self):
        return "{}%".format(self.allocation)

    @property
    def is_contradicting(self):
        return any([self.is_contradicting_field(F)
                    for F in self.PROJECT_FIELDS])

    def is_contradicting_field(self, field_name):
        if hasattr(self, field_name) and hasattr(self.request,
                                                 field_name):
            return not getattr(self, field_name) == getattr(
                self.request, field_name)
        else:
            return False

    def get_absolute_url(self):
        return reverse('staffing:requests:response_details', args=(
            self.request.id, self.id))

    def get_notification_receivers(self):
        vendor_staff = self.proposed.all()
        client_staff = self.request.project.staff.all()
        return set(list(vendor_staff) +
                   [self.posted_by] +
                   list(client_staff) +
                   [self.request.created_by])

    def send_notification(self, created, recipient, **kwargs):
        data = dict(sender=self.posted_by,
                    target=self,
                    action_object=self.request,
                    description='',
                    recipient=recipient,
                    )
        if created:
            data['verb'] = 'created a staffing response for'
        elif self.accepted:
            data['verb'] = 'accepted a staffing response for'
            # TODO: following query needs a detailed look.
            data['sender'] = self.staffed.filter(
                request=self.request,
                project=self.request.project
            ).first().accepted_by
        else:
            data['verb'] = 'updated a staffing response for'
            if kwargs.get('sender'):
                data['sender'] = kwargs.get('sender')
        notify.send(**data)

    def send_notification_email(self, created, email):
        url = ''.join([settings.DEFAULT_HTTP_PROTOCOL,
                       connection.tenant.domain_url])
        cats = self.request.categories.values_list('name', flat=True)
        email_context = {'url': ''.join([url, self.get_absolute_url()]),
                         'created': created,
                         'response': self,
                         'request': self.request,
                         'num_resources': self.request.num_resources,
                         'skills': ','.join(cats),
                         }
        send_notification_mail('emails/staffing_response',
                               [email], email_context)


class ProposedResourceStatus(models.Model):
    PERMISSIONS = (
        ('manage_status', 'Can manage staffing status', Permission.ALL, False),
    )
    CANCELLED = 1
    FAILED = 2
    INITIATED = 3
    IN_PROGRESS = 4
    SUCCESS = 5

    CHOICES = (
        (INITIATED, 'Initiated'),
        (CANCELLED, 'Cancelled',),
        (FAILED, 'Failed',),
        (IN_PROGRESS, 'In progress',),
        (SUCCESS, 'Success',)
    )

    CSS_CLASSES = {
        CANCELLED: 'secondary',
        FAILED: 'danger',
        INITIATED: 'secondary',
        IN_PROGRESS: 'warning',
        SUCCESS: 'success',
    }

    name = models.CharField(max_length=127,
                            help_text='Unique name for the status')

    vendor_name = models.CharField(_('Organizations alias'), default='',
                                   blank=True, max_length=127,
                                   help_text='If other organizations '
                                             'should see a different name? '
                                             'Leave blank to use the same '
                                             'as above.')

    slug = AutoSlugField(populate_from='name', unique=True, always_update=True)

    value = models.PositiveSmallIntegerField(
        choices=CHOICES, default=INITIATED,
        help_text='The state this status represents. This will help the '
        'system provide meaningful analytics to you and make smart '
        'decisions for you. <strong>Initiated</strong> can be set by vendors '
        'while proposing resources.')
    forwards = models.ManyToManyField('self', symmetrical=False,
                                      through='StatusFlow',
                                      help_text='Which status can this '
                                      'status change to')

    class Meta:
        ordering = ('-value',)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('projects:status:details', args=(self.id,))

    @property
    def is_success(self):
        return self.value == self.SUCCESS

    def get_value_code(self):
        return slugify(self.get_value_display())

    def get_css_class(self):
        return self.CSS_CLASSES.get(self.value, 'default')

    def is_allowed_to_use(self, user):
        if user.is_client and user.has_perm('projects.add_project'):
            return True
        elif user.is_vendor and not self.restricted:
            return True

    def get_possible_forward_statuses(self, user, proposal):
        if not user.has_perm('projects.add_proposedresource'):
            return ProposedResourceStatus.objects.none()
        q = Q(driver=StatusFlow.DRIVER_ALL)
        if user.is_vendor:
            q = q | Q(driver=StatusFlow.DRIVER_VENDOR)
        else:
            q = q | Q(driver=StatusFlow.DRIVER_CLIENT)

        valid_flows = self.forward_flows.filter(q)
        return ProposedResourceStatus.objects.filter(
            backward_flows=valid_flows)


class StatusFlow(models.Model):
    DRIVER_CLIENT = 1
    DRIVER_VENDOR = 2
    DRIVER_ALL = 3
    DRIVER_CHOICES = (
        (DRIVER_CLIENT, 'Clients',),
        (DRIVER_VENDOR, 'Vendors',),
        (DRIVER_ALL, 'Everyone',),
    )

    backward = models.ForeignKey(ProposedResourceStatus,
                                 related_name='forward_flows')
    forward = models.ForeignKey(ProposedResourceStatus,
                                related_name='backward_flows')
    driver = models.PositiveSmallIntegerField(choices=DRIVER_CHOICES,
                                              default=DRIVER_CLIENT,
                                              help_text='Who can make this '
                                              'change')

    class Meta:
        unique_together = (('backward', 'forward',),)


class ProposedResource(models.Model, DurationMixin):
    PERMISSIONS = (
        ('add_proposedresource', 'Can change proposed resource status',
         Permission.ALL, False),
    )
    # M2M Fields
    resource = models.ForeignKey('users.User',
                                 related_name='proposed')
    # Can be False if the proposal is actually just a busy slot
    project = models.ForeignKey(Project, related_name='proposals',
                                null=True)

    # Extra rels
    request = models.ForeignKey(StaffingRequest, related_name='proposed',
                                null=True)
    role = models.ForeignKey('roles.Role', null=True, related_name='proposals')
    skill_level = models.ForeignKey('categories.SkillLevel', null=True)
    location = models.ForeignKey('locations.Location', null=True)
    rate_card = models.ForeignKey(Rate, null=True)

    # Details
    final_rate = models.DecimalField(null=True, blank=True,
                                     decimal_places=0, max_digits=10)
    allocation = models.PositiveSmallIntegerField(
        _('Allocation (%)'), default=100)
    start_date = models.DateField(blank=False, null=True)
    end_date = models.DateField(blank=False, null=True)

    channels = GenericRelation(Channel)

    reviews = ReviewsField(Review, average_field=None, count_field=None)

    # State
    status = models.ForeignKey('ProposedResourceStatus', null=True,
                               related_name='proposed_resources')
    #status_changed_at = MonitorField(monitor='status')
    status_changed_at = models.DateTimeField(null=True)
    changed_by = models.ForeignKey('users.User',
                                   related_name='edited_resources')
    created_by = models.ForeignKey('users.User',
                                   related_name='created_by')

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    metric = GenericRelation(Metric)
    objects = hstore.HStoreManager()
    tracker = FieldTracker(fields=['final_rate', 'status', 'allocation',
                                   'start_date', 'end_date'])

    class Meta:
        unique_together = (('project', 'resource', 'request', 'role',
                            'skill_level', 'location'),)
        ordering = ('-status__value',)

    def save(self, *args, **kwargs):
        if self.request:
            self.project = self.request.project
        if self.tracker.has_changed('status'):
            self.status_changed_at = now()
        self.update_final_rate()
        if self.tracker.has_changed('status'):
            self.status_changed_at = now()
        return super(ProposedResource, self).save(*args, **kwargs)

    def get_short_title(self):
        if self.resource.vendor:
            return '{} ({})'.format(self.resource.get_name_display(), self.resource.vendor)
        else:
            return self.resource.get_name_display()

    def get_status_value(self):
        if self.status:
            return self.status.get_css_class()
        else:
            return 'default'

    def get_channel_vendor_choices(self, user):
        vendor = user.vendor or self.resource.vendor
        if vendor:
            return ((vendor.id, vendor.name,),)
        else:
            return tuple()

    def get_channel_notification_users(self, channel):
        """Should return a queryset or a list.
        Users returned will be notified when a channel has a new message"""
        users = [self.changed_by.id]
        if self.resource.has_joined:
            users.append(self.resource.id)
        return users

    def get_comments_count(self):
        return Message.objects.filter(
            channel__content_type=ContentType.objects.get_for_model(self),
            channel__object_id=self.id
        ).count()

    def post_event_object_delete(self, user):
        pass

    def create_event_object(self, user):
        content_type = ContentType.objects.get_for_model(ProposedResource)
        Event.objects.get_or_create(user=user,
                                    content_type_id=content_type.id,
                                    object_id=self.id,)
        if self.request:
            self.request.create_event_object(user=user)

    @classmethod
    def get_accepted_count(self, vendor):
        proposed_count = self.objects.filter(resource__vendor=vendor).count()
        accepted_count = self.objects.filter(resource__vendor=vendor,
                                             status__value=
                                             ProposedResourceStatus.SUCCESS)\
            .count()

        return float(accepted_count) / proposed_count

    @property
    def is_staffed(self):
        return self.status and self.status.is_success

    @property
    def staffed_at(self):
        return self.status_changed_at

    def get_absolute_url(self):
        return reverse('staffing:proposed_resource_details',
                       args=(self.id,))

    def get_delete_url(self):
        return reverse('staffing:delete_proposed_resource',
                       args=(self.id,))

    def clean_fields(self, exclude=None):
        exclude = exclude or []
        self.update_final_rate()
        super(ProposedResource, self).clean_fields(exclude)
        DurationMixin.clean_fields(self, exclude)
        if self.final_rate and self.final_rate < 0:
            raise ValidationError('Rate cannot be negative')

    def __Reviews__denorm_reviews__(self, commit=True):
        self.resource.__Reviews__denorm_reviews__(commit)

    def __update_response(self):
        pass

    def update_final_rate(self):
        self.final_rate = self.total_cost(force_calculate=True)

    @property
    def natural_start_date(self):
        return humanized_date(self.start_date)

    @property
    def natural_end_date(self):
        return humanized_date(self.end_date)

    @property
    def num_days(self):
        return days_in_date_range(self.start_date, self.end_date)

    @property
    def hours_per_day(self):
        return int(round(8 * (self.allocation / 100)))

    @property
    def hourly_rate(self):
        return self.final_rate / (self.hours_per_day * self.num_days)

    def rate(self, force_calculate=False):
        if not force_calculate:
            return MockRate(self.final_rate, is_fixed=False)
        else:
            return self.rate_card

    def total_cost(self, force_calculate=False):
        if not force_calculate:
            return self.final_rate
        rate = self.rate(force_calculate)
        if rate:
            return int(rate.cost * self.num_days * self.hours_per_day)
        return 0

    def total_cost_display(self):
        return self.total_cost() or ''

    def get_core_cost_calculation_display(self):
        rate = self.rate(force_calculate=True)
        if rate and not rate.is_fixed_rate:
            return mark_safe(
                "<i class='fa fa-dollar text-muted'></i> {rate}<small> an hour</small>"
                " &times; {num_days} <small class='text-muted'> days</small>"
                " &times; {hours} <small> hours a day</small>"
            ).format(
                rate=rate.cost,
                num_days=self.num_days,
                hours=self.hours_per_day,
                perm_url=reverse('groups:list')
            )
        return ''
    get_core_cost_calculation_display.allow_tags = True

    def get_cost_calculation_display_sans_help_text(self):
        display = self.get_core_cost_calculation_display()
        if display:
            return mark_safe(
                "<span style='wrap:nowrap'>"
                "{display}"
                "</span>"
            ).format(
                display=display,
            )
        return ''
    get_cost_calculation_display_sans_help_text.allow_tags = True

    def get_cost_calculation_display(self):
        display = self.get_core_cost_calculation_display()
        if display:
            return mark_safe(
                "<span style='wrap:nowrap'>"
                "{display}"
                "<hr class='thin'><small class='text-muted'>Only visible to"
                " those with <strong>'Can view financial information'</strong> permission."
                " See <a href='{perm_url}'>Permissions and Groups</a>."
                "</small>"
                "</span>"
            ).format(
                display=display,
                perm_url=reverse('groups:list')
            )
        return ''
    get_cost_calculation_display.allow_tags = True

    def is_accepted(self):
        return self.status and self.status.is_success


class DeliverableResponse(models.Model, SerializableMixin):
    PERMISSIONS = (
        ('add_staffingresponse', 'Can add staffing response',
         Permission.ALL, False),
    )

    STATUS_DRAFT = 1
    STATUS_SENT = 2
    STATUS_CHOICES = (
        (STATUS_DRAFT, 'draft'),
        (STATUS_SENT, 'sent'),
    )

    rate = models.DecimalField(null=True,
                               decimal_places=0, max_digits=10)

    request = models.ForeignKey(StaffingRequest, related_name='deliverable')
    vendor = models.ForeignKey(Vendor, related_name='deliverable', null=True)

    posted_by = models.ForeignKey('users.User',
                                  related_name='posted_deliverable')
    allocation = models.PositiveSmallIntegerField(
        _('Allocation (%)'), default=100)
    location = models.ForeignKey('locations.Location', null=True)

    # Reccords who accepted a fixed price project
    is_accepted = models.BooleanField(default=False)
    accepted_by = models.ForeignKey('users.User',
                                    related_name='accepted_deliverable',
                                    blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    description = models.TextField(_('Description'), blank=True)

    handlers = models.ManyToManyField('users.User',
                                      related_name='handled_deliverables',
                                      blank=True)

    tracker = FieldTracker()

    objects = models.Manager()

    def __unicode__(self):
        if self.id and self.request:
            ret = '{}'.format(self.request)
        else:
            ret = 'staffing response'
        return ret

    def save(self, *args, **kwargs):
        if self.accepted_by:
            self.is_accepted = True
        ret = super(DeliverableResponse, self).save(*args, **kwargs)
        return ret

    def clean_fields(self, exclude=None):
        exclude = exclude or []
        super(DeliverableResponse, self).clean_fields(exclude)
        if self.rate and self.rate < 0:
            raise ValidationError('Rate cannot be negative')

    def total_cost(self):
        return self.rate

    @property
    def total_proposed_cost(self):
        if self.request.is_fixed_price:
            return self.rate
        staffed = self.proposed.filter()
        if staffed.exists():
            cost = 0
            for staff in staffed.all():
                cost += staff.total_cost()
            return cost
        return None

    @property
    def accepted(self):
        return self.is_accepted

    @property
    def natural_modified_date(self):
        return humanized_datetime(self.modified)

    def get_allocation_display(self):
        return "{}%".format(self.allocation)

    @property
    def is_contradicting(self):
        return any([self.is_contradicting_field(F)
                    for F in self.PROJECT_FIELDS])

    def is_contradicting_field(self, field_name):
        if hasattr(self, field_name) and hasattr(self.request,
                                                 field_name):
            return not getattr(self, field_name) == getattr(
                self.request, field_name)
        else:
            return False

    def get_absolute_url(self):
        return reverse('staffing:requests:response_details', args=(
            self.request.id, self.id))

    def get_notification_receivers(self):
        vendor_staff = self.proposed.all()
        client_staff = self.request.project.staff.all()
        return set(list(vendor_staff) +
                   [self.posted_by] +
                   list(client_staff) +
                   [self.request.created_by])
