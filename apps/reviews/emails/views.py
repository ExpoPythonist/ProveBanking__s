from django.conf import settings

from med_social.utils import get_absolute_url
from med_social.libs.template import BaseEmailTemplateView


class NewReviewEmail(BaseEmailTemplateView):
    subject_template_name =\
        'emails/review/subject.txt'
    body_template_name =\
        'emails/review/message.txt'
    html_body_template_name =\
        'emails/review/email.html'

    def __init__(self, user, review, recipient, anonymous=False,
                 *args, **kwargs):
        self.user = user
        self.review = review
        self.recipient = recipient
        self.anonymous = anonymous

        super(NewReviewEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(NewReviewEmail, self).get_context_data(**kwargs)
        ctx['anonymous'] = self.anonymous
        ctx['user'] = self.user
        ctx['recipient'] = self.recipient
        ctx['review'] = self.review
        ctx['resource_url'] = get_absolute_url(
            self.review.get_absolute_url())
        return ctx

    def render_to_message(self, *args, **kwargs):
        if not self.anonymous:
            kwargs['from_email'] = "{username} {email}"\
                .format(username=self.user.get_name_display(),
                        email=settings.NO_REPLY_EMAIL)

        kwargs['to'] = (self.recipient.email,)
        return super(NewReviewEmail, self).render_to_message(*args, **kwargs)


class ReviewTokenEmail(BaseEmailTemplateView):
    subject_template_name =\
        'emails/review_token/subject.txt'
    body_template_name =\
        'emails/review_token/message.txt'
    html_body_template_name =\
        'emails/review_token/email.html'

    def __init__(self, review_token, *args, **kwargs):
        self.review_token = review_token
        super(ReviewTokenEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super(ReviewTokenEmail, self).get_context_data(**kwargs)
        ctx['token'] = self.review_token
        ctx['token_url'] = get_absolute_url(self.review_token.get_create_review_url())
        ctx['tenant_url'] = get_absolute_url('/')
        return ctx

    def render_to_message(self, *args, **kwargs):
        username = 'Intuit Sourcing'
        if self.review_token.created_by:
            username = self.review_token.created_by.get_name_display()
        kwargs['from_email'] = "{username} {email}"\
            .format(username=username,
                    email=settings.NO_REPLY_EMAIL)
        kwargs['to'] = (self.review_token.email,)
        return super(ReviewTokenEmail, self).render_to_message(*args, **kwargs)
