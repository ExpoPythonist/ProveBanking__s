from django.db import models
from django.db.models import F, Sum
from django.contrib.contenttypes.models import ContentType
from django.utils.timezone import now

from djorm_pgarray.fields import DateTimeArrayField
from filtered_contenttypes.fields import FilteredGenericForeignKey
from model_utils import FieldTracker


def _default_views():
    return []


class PageView(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    item = FilteredGenericForeignKey('content_type', 'object_id')

    by = models.ForeignKey('users.User', related_name='page_views')
    count = models.IntegerField(default=1)
    views = DateTimeArrayField(default=_default_views)

    tracker = FieldTracker(fields=['views', ])

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        index_together = (('content_type', 'object_id',),)
        unique_together = (('content_type', 'object_id', 'by',),)

    def save(self, *args, **kwargs):
        if self.tracker.has_changed('views'):
            self.count = len(self.views)
        return super(PageView, self).save(*args, **kwargs)

    @classmethod
    def add_view(klass, request, item, timestamp=None):
        timestamp = timestamp or now()

        if not request.user.is_authenticated():
            return
        view, created = klass.objects.get_or_create(
            item=item, by=request.user, defaults={'views': [timestamp]})
        if not created:
            view.views = view.views or []
            view.views.insert(0, timestamp)
            view.save(update_fields=('count', 'views'))

    @classmethod
    def get_views_count(klass, item):
        return klass.objects.filter(item=item).aggregate(
            sum=Sum('count'))['sum'] or 0

    @classmethod
    def get_unique_views_count(klass, item):
        return klass.objects.filter(item=item).count()

    def get_sort_key(self):
        return self.updated_at
