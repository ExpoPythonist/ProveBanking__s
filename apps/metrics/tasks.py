import datetime

from dateutil.relativedelta import relativedelta

from django.utils.timezone import now
from django.db.models import Avg
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.models import ContentType

from annoying.functions import get_object_or_None
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from django_atomic_celery import task
from tenant_schemas.utils import tenant_context, get_tenant_model

from vendors.tasks import aggregate_metric_for_vendor, vendor_user_rating
from projects.tasks import (req_vendor_response_metric,
                            proposed_acceptance_metric)


@task
def aggregate_metric_for_object(tenant_id, object_id, content_type, kind):
    tenant = get_object_or_None(get_tenant_model(), id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        try:
            content_type_obj = ContentType.objects.get_for_id(content_type)
        except ContentType.DoesNotExist:
            return

        try:
            content_object = content_type_obj.get_object_for_this_type(pk=object_id)
        except ObjectDoesNotExist:
            return

        last_month = now() - relativedelta(months=1)
        last_month_first_date = datetime.date(day=1, month=last_month.month, year=last_month.year)

        if hasattr(content_object, 'metric_owned'):
            response_metric_avg = content_object.metric_owned.filter(
                kind=kind, created__month=last_month.month,).aggregate(Avg('score'))

            if response_metric_avg['score__avg']:
                content_object.metric_aggregate.create(
                    kind=kind, start_date=last_month_first_date, score=response_metric_avg['score__avg'])


@task
def create_metric(tenant_id, object_id, content_type, target_type, target_id, kind, score):
    tenant = get_object_or_None(get_tenant_model(), id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        try:
            content_type_obj = ContentType.objects.get_for_id(content_type)
            target_type_obj = ContentType.objects.get_for_id(target_type)
        except ContentType.DoesNotExist:
            return

        try:
            content_object = content_type_obj.get_object_for_this_type(pk=object_id)
            target_object = target_type_obj.get_object_for_this_type(pk=target_id)
        except ObjectDoesNotExist:
            return

        content_object.metric.create(kind=kind, score=score, target_object=target_object)


@periodic_task(run_every=(crontab(0, 0, day_of_month='1')), ignore_result=True)
def aggregate_metric_task():
    for tenant in get_tenant_model().objects.all():
        aggregate_metric_for_vendor.delay(tenant_id=tenant.id)


@periodic_task(run_every=(crontab(minute=0, hour='*/3')), ignore_result=True)
def create_metric_scheduler():
    for tenant in get_tenant_model().objects.all():
        req_vendor_response_metric.delay(tenant_id=tenant.id)
        proposed_acceptance_metric.delay(tenant_id=tenant.id)


@periodic_task(run_every=(crontab(0, 4, day_of_month='1')), ignore_result=True)
def create_user_metric_scheduler():
    for tenant in get_tenant_model().objects.all():
        vendor_user_rating.delay(tenant_id=tenant.id)
