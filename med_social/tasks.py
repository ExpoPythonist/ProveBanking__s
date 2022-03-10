from celery import task
from tenant_schemas.utils import tenant_context


@task
def send_all_notification_task(tenant, **kwargs):
    with tenant_context(tenant):
        pk = kwargs.pop('instance_id')
        model = kwargs.pop('model')
        created = kwargs.pop('created', False)
        send_email = kwargs.pop('send_email', True)
        instance = model.objects.get(id=pk)
        recipients = instance.get_notification_receivers()
        for recipient in recipients:
            instance.send_notification(created=created,
                                       recipient=recipient, **kwargs)
            if send_email:
                instance.send_notification_email(created=created,
                                            email=recipient.email, **kwargs)
