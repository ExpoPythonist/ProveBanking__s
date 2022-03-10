import json
import requests
from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_save, post_delete

from med_social.utils import get_current_tenant
from notifications.models import Notification
from post_office import mail
from vendors.rfp_models import RFP, Bid, Message


@receiver(post_save, sender=Notification, dispatch_uid='notify_email_or_text')
def notify_email_or_text(sender, **kwargs):
    notification = kwargs['instance']

    if not kwargs['created'] or kwargs['raw']:
        return

    community = get_current_tenant()

    if notification.recipient.username == 'kevin':
        SLACK_WEBHOOK = 'https://hooks.slack.com/services/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'
        if notification.target and hasattr(notification.target, 'get_absolute_url'):
            link = notification.target.get_absolute_url()
        elif notification.action_object and hasattr(notification.action_object, 'get_absolute_url'):
            link = notification.action_object.get_absolute_url()
        else:
            link = notification.actor.get_absolute_url()
        requests.post(SLACK_WEBHOOK, {'payload': json.dumps({'text': u'{} {}'.format(unicode(notification), community.get_full_url() + link)})})

        if notification.action_object.__class__ in (RFP, Bid, Message):
            user = notification.recipient
            mail.send(user.email, template='New RFP Notification', context={'notification': notification, 'community': community})
