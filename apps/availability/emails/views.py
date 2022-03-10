from django.core.urlresolvers import reverse
from mailviews.messages import TemplatedHTMLEmailMessageView

from med_social.utils import get_absolute_url


class RequestUpdateEmail(TemplatedHTMLEmailMessageView):
    subject_template_name = 'availability/emails/request_update_subject.txt'
    body_template_name = 'availability/emails/request_update_body.txt'
    html_body_template_name = 'availability/emails/request_update_body.html'

    def __init__(self, user, requested_by, *args, **kwargs):
        self.user = user
        self.requested_by = requested_by
        super(RequestUpdateEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(RequestUpdateEmail, self).get_context_data(**kwargs)
        ctx['user'] = self.user
        ctx['requested_by'] = self.requested_by
        ctx['availability'] = self.user.get_availability_as_weeks()
        ctx['confirm_url'] = get_absolute_url(reverse('availability:confirm'))
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = (self.user.email,)
        return super(RequestUpdateEmail, self).render_to_message(*args, **kwargs)
