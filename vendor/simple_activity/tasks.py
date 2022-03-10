from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from annoying.functions import get_object_or_None
from celery import task
from tenant_schemas.utils import tenant_context

from customers.models import Customer


@task
def event_generator(tenant_id, user_list, object_id, content_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        try:
            content_type_object = ContentType.objects.get(id=content_id)
            content_object = content_type_object\
                .get_object_for_this_type(id=object_id)

        except ObjectDoesNotExist:
            return

        recipients = get_user_model().objects.filter(id__in=user_list)

        for recipient in recipients:
            content_object.create_event_object(user=recipient)
