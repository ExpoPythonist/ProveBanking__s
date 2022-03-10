import datetime

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now


from annoying.functions import get_object_or_None
from celery import task
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from tenant_schemas.utils import tenant_context

from med_social.utils import track_event

from customers.models import Customer
from users.models import User


@task
def event_generator(tenant_id, user_list, object_id, content_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        try:
            content_type_object = ContentType.objects.get(id=content_id)
            content_object = content_type_object.get_object_for_this_type(id=object_id)

        except ObjectDoesNotExist:
            return

        recipients = get_user_model().objects.filter(id__in=user_list)

        for recipient in recipients:
            content_object.create_event_object(user=recipient)


@task  # @periodic_task(run_every=(crontab(minute=0, hour=23, day_of_week='fri')), ignore_result=True)
def weekly_activity_schedule():
    tenant = Customer.objects.get(schema_name='intuit')
    with tenant_context(tenant):
        a = now()
        c = a - datetime.timedelta(days=7)
        user_list = User.objects.exclude(last_login__lte=c).order_by('kind')

        for user in user_list:

            pageview = user.page_views.all()
            a = list()
            i = 0

            if user.first_login == user.last_login:
                first_login = "True"
            else:
                first_login = "False"

            for obj in pageview:

                view_count = 0
                for time in obj.views:
                    if time > c:
                        view_count = view_count + 1
                    i = i + view_count

                if view_count:
                    a.append(str(obj.item) + ":" + str(view_count))

            pageview = user.page_views.all()

            track_event('Weekly Tracking: Intuit', {
                'user_id': user.id,
                'username': user.username,
                'user_kind': user.kind,
                'view_details': ",".join(a),
                'total_views': str(i),
                'first_login': first_login,
            })
