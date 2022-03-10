from django.conf import settings

from med_social.utils import get_absolute_url
from med_social.libs.template import BaseEmailTemplateView

from projects.models import StaffingRequest


class MentionEmail(BaseEmailTemplateView):
    pass


class NewMessageEmail(BaseEmailTemplateView):
    subject_template_name = 'channels/emails/new_message_subject.txt'
    body_template_name = 'channels/emails/new_message_body.txt'
    html_body_template_name = 'channels/emails/new_message_body.html'

    def __init__(self, user, message, *args, **kwargs):
        self.user = user
        self.message = message
        super(NewMessageEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(NewMessageEmail, self).get_context_data(**kwargs)
        ctx['user'] = self.user
        ctx['message'] = self.message
        if isinstance(self.message.channel.content_object, StaffingRequest):
            ctx['staffing_req'] = self.message.channel.content_object
            ctx['project'] = self.message.channel.content_object.project
            ctx['project_url'] = get_absolute_url(self.message.channel
                                                  .content_object.project
                                                  .get_absolute_url())
            ctx['staffing_req_url'] = "{url}?active_tab=channel-{id}"\
                .format(url=
                        get_absolute_url(self.message.channel.content_object
                                         .get_absolute_url()),
                        id=self.message.channel.id)

        ctx['discussion_url'] = get_absolute_url(
            self.message.get_absolute_url())
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = (self.user.email,)
        kwargs['from_email'] = "{username} {email}"\
            .format(username=self.message.posted_by.get_name_display(),
                    email=settings.NO_REPLY_EMAIL)
        return super(NewMessageEmail, self).render_to_message(*args, **kwargs)
