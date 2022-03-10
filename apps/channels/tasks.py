from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from annoying.functions import get_object_or_None

from django_atomic_celery import task
from notifications.signals import notify
from tenant_schemas.utils import tenant_context

from activity.tasks import event_generator
from customers.models import Customer
from projects.models import StaffingRequest

from .models import Message
from .emails.views import NewMessageEmail


@task
def new_message(tenant_id, message_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return

    with tenant_context(tenant):
        message = get_object_or_None(Message, id=message_id)
        if not message:
            return

        channel = message.channel
        if hasattr(channel.content_object, 'get_channel_notification_users'):
            recipients = list(channel.content_object
                              .get_channel_notification_users(channel))
        else:
            recipients = []

        mentioned = message.mentions.all()
        recipients = get_user_model().objects.filter(
            id__in=recipients
        ).exclude(id__in=mentioned.values_list('id', flat=True))

        recipient_list = [recipient.id for recipient in recipients]
        mentions_list = [mention.id for mention in mentioned]

        recipient_list.extend(mentions_list)

        if message.posted_by.id in recipient_list:
            recipient_list.remove(message.posted_by.id)

        content_id = ContentType.objects.get_for_model(message.channel).id

        event_generator.delay(tenant_id=tenant_id,
                              user_list=recipient_list,
                              object_id=message.channel.id,
                              content_id=content_id
                              )

        for mentioned in mentioned:
            if mentioned == message.posted_by:
                continue
            notify.send(
                sender=message.posted_by,
                verb='mentioned you in a comment',
                target=None,
                action_object=message,
                description='"{}"'.format(message.body),
                recipient=mentioned
            )
            #MentionEmail(user=mentioned, message=message).send()
            NewMessageEmail(user=mentioned, message=message).send()

        for recipient in recipients:
            if recipient == message.posted_by:
                continue

            data = dict(sender=message.posted_by,
                        target=None,
                        action_object=message,
                        description='"{}"'.format(message.body),
                        recipient=recipient)

            if isinstance(message.channel.content_object, StaffingRequest):
                data['verb'] = 'commented on {project}'\
                    .format(project=message.channel.content_object.project)
            else:
                data['verb'] = 'commented on a'
                data['target'] = channel

            notify.send(**data)
            NewMessageEmail(user=recipient, message=message).send()


@task
def new_channel(channel):
    pass
