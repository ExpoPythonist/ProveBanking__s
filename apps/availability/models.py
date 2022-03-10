import datetime

from django.db import models
from django.db.models import Sum, Q
from django.utils.timezone import now
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from projects.models import ProposedResource, ProposedResourceStatus


class Week(models.Model):
    date = models.DateField()
    allocation = models.IntegerField(default=0)
    user = models.ForeignKey('users.User', related_name='availability_weeks')
    proposed = models.ManyToManyField('projects.ProposedResource', related_name='availability_weeks')

    class Meta:
        unique_together = (('user', 'date'),)
        ordering = ('date',)

    def __unicode__(self):
        return '{}% for {}'.format(self.allocation, self.date.strftime('%d %B, %Y'))

    @property
    def month(self):
        return self.date.month

    @classmethod
    def create_from_proposal(cls, proposed):
        if proposed.status and not proposed.is_staffed:
            return

        if not proposed.start_date or not proposed.end_date:
            return

        user = proposed.resource
        weeks = []
        end_date = proposed.end_date
        last_week = end_date - datetime.timedelta(days=end_date.weekday())

        date = proposed.start_date - datetime.timedelta(days=proposed.start_date.weekday())

        start_of_week = date - datetime.timedelta(days=date.weekday())

        allocations = []
        while start_of_week <= last_week:
            weeks.append(start_of_week)
            allocation, created = cls.objects.get_or_create(
                user=user, date=start_of_week, defaults={'allocation': proposed.allocation})

            if not allocation.proposed.filter(id=proposed.id).exists():
                allocation.proposed.add(proposed)
            allocations.append(allocation)
            start_of_week = start_of_week + datetime.timedelta(days=7)
        return allocations

    def add_proposal(self, proposed):
        week_end = self.date.replace(day=self.date.day + 6)
        contains_date = proposed.start_date <= self.date <= proposed.end_date
        starts_in_week = self.date <= proposed.start_date <= week_end
        ends_in_week = self.date <= proposed.end_date <= week_end

        if any(contains_date, starts_in_week, ends_in_week):
            if not self.proposed.filter(id=proposed.id).exists():
                self.proposed.add(proposed)
                self.allocation += proposed.allocation
                self.save()

    def update_allocation(self):
        self.allocation = self.proposed.filter(
            Q(status__value=ProposedResourceStatus.SUCCESS) | Q(status__isnull=True)
        ).aggregate(Sum('allocation'))['allocation__sum'] or 0


class UpdateRequest(models.Model):
    user = models.ForeignKey('users.User', related_name='update_requests')
    requested_by = models.ManyToManyField('users.User', related_name='requested_availability_updates')


@receiver(post_delete, sender=ProposedResource, dispatch_uid='availability.proposedresource.post_delete')
def post_delete_proposed_resource(**kwargs):
    instance = kwargs['instance']

    resource = instance.resource
    resource.last_updated_availability = now()
    resource.next_available = resource.calculate_next_available_date()
    resource.save(update_fields=('meta', 'next_available'))

    if instance.start_date and instance.end_date:
        for week in Week.objects.filter(date__gte=instance.start_date, date__lte=instance.end_date):
            week.update_allocation()
            week.save(update_fields=('allocation',))


@receiver(post_save, sender=ProposedResource, dispatch_uid='availability.proposedresource.post_save')
def post_save_proposed_resource(**kwargs):
    instance = kwargs['instance']
    created = kwargs.get('created')

    resource = instance.resource
    resource.last_updated_availability = now()
    resource.next_available = resource.calculate_next_available_date()
    resource.save(update_fields=('meta', 'next_available'))

    if created:
        Week.create_from_proposal(instance)

    if not instance.tracker.changed():
        return

    if not (instance.start_date or instance.end_date):
        return

    q = Q(id__in=instance.availability_weeks.values_list('id', flat=True))
    if instance.tracker.has_changed('status'):
        if instance.is_staffed or not instance.status:
            Week.create_from_proposal(instance)
        else:
            instance.availability_weeks.clear()

    q = q | Q(date__gte=instance.start_date, date__lte=instance.end_date)

    if instance.tracker.has_changed('start_date') or instance.tracker.has_changed('end_date'):
        start_date = instance.tracker.changed().get('start_date') or instance.start_date
        end_date = instance.tracker.changed().get('end_date') or instance.end_date
        q = q | Q(date__gte=start_date, date__lte=end_date)

    for_resource = Q(user=instance.resource)
    q = q & for_resource

    weeks = Week.objects.filter(q)
    if instance.is_staffed or not instance.status:
        to_keep = weeks.filter(date__gte=instance.start_date, date__lte=instance.end_date).values_list('id', flat=True)
        to_remove = weeks.exclude(id__in=to_keep).values_list('id', flat=True)
        instance.availability_weeks.remove(*to_remove)
        instance.availability_weeks.add(*to_keep)
    else:
        instance.availability_weeks.clear()

    for week in weeks:
        week.update_allocation()
        week.save(update_fields=('allocation',))

    Week.create_from_proposal(instance)
