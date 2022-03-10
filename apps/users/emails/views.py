from django.conf import settings
from django.core.urlresolvers import reverse

from med_social.libs.template import BaseEmailTemplateView
from med_social.utils import get_absolute_url


class UserInvitationEmail(BaseEmailTemplateView):
    subject_template_name =\
        'users/emails/invitation_subject.txt'
    body_template_name =\
        'users/emails/invitation_message.txt'
    html_body_template_name =\
        'users/emails/invitation_email.html'

    def __init__(self, username, recipient, password,
                 direct_url, url, sender, reset_password_url,
                 message, *args, **kwargs):

        self.username = username
        self.recipient = recipient
        self.password = password
        self.direct_url = direct_url
        self.url = url
        self.sender = sender
        self.reset_password_url = reset_password_url
        self.message = message
        super(UserInvitationEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(UserInvitationEmail, self).get_context_data(**kwargs)
        ctx['recipient'] = self.recipient
        ctx['direct_url'] = self.direct_url
        ctx['url'] = self.url
        ctx['sender'] = self.sender
        ctx['reset_password_url'] = self.reset_password_url
        ctx['tenant_url'] = get_absolute_url(reverse('home'))
        ctx['message'] = self.message
        return ctx

    def render_to_message(self, *args, **kwargs):

        kwargs['to'] = (self.recipient,)
        kwargs['from_email'] = "{username} {email}"\
            .format(username=self.sender.get_name_display(),
                    email=settings.NO_REPLY_EMAIL)
        return super(UserInvitationEmail, self).render_to_message(*args,
                                                                  **kwargs)


class UserSignupEmail(BaseEmailTemplateView):
    subject_template_name =\
        'users/emails/signup/subject.txt'
    body_template_name =\
        'users/emails/signup/message.txt'
    html_body_template_name =\
        'users/emails/signup/email.html'

    def __init__(self, recipient,
                 direct_url, *args, **kwargs):

        self.recipient = recipient
        self.direct_url = direct_url
        super(UserSignupEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(UserSignupEmail, self).get_context_data(**kwargs)
        ctx['recipient'] = self.recipient
        ctx['direct_url'] = self.direct_url
        ctx['tenant_url'] = get_absolute_url(reverse('home'))
        return ctx

    def render_to_message(self, *args, **kwargs):

        kwargs['to'] = (self.recipient,)
        # kwargs['from_email'] = "{username} {email}"\
        #     .format(username=self.sender.get_name_display(),
        #             email=settings.NO_REPLY_EMAIL)
        return super(UserSignupEmail, self).render_to_message(*args,
                                                              **kwargs)
