from mailviews.messages import TemplatedHTMLEmailMessageView
from post_office import mail

from ..utils import get_current_tenant


class BaseEmailTemplateView(TemplatedHTMLEmailMessageView):

    def get_context_data(self, *args, **kwargs):
        context = super(BaseEmailTemplateView, self).\
            get_context_data(*args, **kwargs)
        context['current_tenant'] = get_current_tenant()
        context['proven'] = 'http://proven.cc'
        context['vetted'] = 'http://proven.cc'
        return context

    def send(self, *args, **kwargs):
        """
        Use post_office mail sending
        """
        message = self.render_to_message(*args, **kwargs)

        # use html alternative, if provided
        body = message.body
        for alternative in message.alternatives:
            if alternative and alternative[1].startswith('text/html'):
                body = alternative[0]
                break

        return mail.send(
            message.to,
            message.from_email,
            html_message=body,
            subject=message.subject,
            cc=message.cc
        )
