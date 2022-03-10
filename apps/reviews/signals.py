from django.db import connection
from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_save, post_init
from med_social.utils import track_event

from analytics.models import PageView

from .models import Review, ReviewToken
from .tasks import new_review, new_review_token


@receiver(post_save, sender=Review, dispatch_uid='reviews.review_notifications.post_save')
def send_Review_notifications(sender, **kwargs):
    if kwargs['raw']:return
    instance = kwargs.get('instance')
    created = kwargs.get('created')
    tenant = connection.get_tenant()
    if created:
        new_review.delay(tenant.id, instance.id)
        if instance.anonymous:
            PageView.objects.filter(item=instance.content_object,
                                    by=instance.posted_by).delete()

        if instance.token:
            track_event(
                'Review:created',
                {
                    'vendor_id': instance.content_object.id,
                    'vendor': instance.content_object.__str__(),
                    'sender': instance.token.email,
                    'is_anonymous': instance.anonymous,

                },
            )
        else:
            track_event(
                'Review:created',
                {
                    'vendor_id': instance.content_object.id,
                    'vendor': instance.content_object.__str__(),
                    'sender': instance.posted_by.get_name_display(),
                    'is_anonymous': instance.anonymous,

                },
            )

        if instance.content_object._meta.model_name == 'vendor':
            instance.score_update()


@receiver(post_init, sender=Review, dispatch_uid='reviews.Review.pre_save')
def post_user_init(sender, **kwargs):
    review = kwargs['instance']
    review._orig_score = review.score


@receiver(post_save, sender=ReviewToken,
          dispatch_uid='reviews.ReviewToken.post_save')
def send_review_token(sender, **kwargs):
    instance = kwargs.get('instance')
    created = kwargs.get('created')
    tenant = connection.get_tenant()
    if created:
        new_review_token.delay(tenant.id, instance.id)
