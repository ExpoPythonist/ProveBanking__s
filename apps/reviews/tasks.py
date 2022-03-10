from annoying.functions import get_object_or_None
from django_atomic_celery import task
from notifications.signals import notify
from tenant_schemas.utils import tenant_context

from customers.models import Customer
from users.models import User

from med_social.utils import get_absolute_url as abs_url
from .models import Review, ReviewToken
from .emails.views import NewReviewEmail, ReviewTokenEmail


@task
def new_review(tenant_id, instance_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        review = get_object_or_None(Review, id=instance_id)

        if not review:
            return

        recipients = review.get_notification_receivers()

        if review.vendor_viewable and review.content_object._meta.model_name == 'vendor':
            for recipient in review.content_object.contacts.all():
                data = dict(sender=review.content_object,
                            action_object=review.content_object,
                            description='',
                            recipient=recipient,
                            verb='was reviewed by someone at {}'.format(tenant.name),
                            )
                notify.send(**data)

                NewReviewEmail(user=review.posted_by,
                               review=review,
                               recipient=recipient,
                               anonymous=True).send()


        if review.anonymous:
            for recipient in recipients:

                data = dict(sender=review.content_object,
                            action_object=review.content_object,
                            description='',
                            recipient=recipient,
                            verb='was reviewed by someone at {}'.format(tenant.name),
                            )
                notify.send(**data)

                NewReviewEmail(user=review.posted_by,
                               review=review,
                               recipient=recipient,
                               anonymous=True).send()
        else:
            for recipient in recipients:

                data = dict(sender=review.posted_by,
                            target=review,
                            action_object=review.content_object,
                            description='',
                            recipient=recipient,
                            verb='added a new review',
                            )
                notify.send(**data)

                NewReviewEmail(user=review.posted_by,
                               review=review,
                               recipient=recipient).send()


@task
def new_review_token(tenant_id, instance_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        review_token = get_object_or_None(ReviewToken, id=instance_id)

        if not review_token:
            return
        ReviewTokenEmail(review_token=review_token).send()
