from django.conf import settings
from django.core.urlresolvers import reverse

from med_social.utils import get_absolute_url
from med_social.libs.template import BaseEmailTemplateView

from ..models import RequestVendorRelationship


class NewResourceEmail(BaseEmailTemplateView):
    subject_template_name =\
        'projects/emails/resource/subject.txt'
    body_template_name =\
        'projects/emails/resource/message.txt'
    html_body_template_name =\
        'projects/emails/resource/email.html'

    def __init__(self, user, recipient, proposed_resource, *args, **kwargs):
        self.user = user
        self.recipient = recipient
        self.proposed_resource = proposed_resource
        super(NewResourceEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(NewResourceEmail, self).get_context_data(**kwargs)
        ctx['user'] = self.user
        ctx['recipient'] = self.recipient
        ctx['proposed_resource'] = self.proposed_resource
        ctx['proposed_resource_url'] = get_absolute_url(
            self.proposed_resource.get_absolute_url())
        if self.proposed_resource.request:
            ctx['staffing_req_url'] = get_absolute_url(
                self.proposed_resource.request.get_absolute_url())
        ctx['project_url'] = get_absolute_url(
            self.proposed_resource.project.get_absolute_url())
        ctx['signature'] = True
        return ctx

    def render_to_message(self, *args, **kwargs):

        kwargs['to'] = (self.recipient.email,)
        kwargs['from_email'] = "{username} {email}"\
            .format(username=self.user.get_name_display(),
                    email=settings.NO_REPLY_EMAIL)
        return super(NewResourceEmail, self).render_to_message(*args, **kwargs)


class ResourceStatusChangeEmail(BaseEmailTemplateView):
    subject_template_name =\
        'projects/emails/status_change/subject.txt'
    body_template_name =\
        'projects/emails/status_change/message.txt'
    html_body_template_name =\
        'projects/emails/status_change/email.html'

    def __init__(self, user, recipient, forwards,
                 proposed_resource, *args, **kwargs):
        self.user = user
        self.recipient = recipient
        self.forwards = forwards
        self.proposed_resource = proposed_resource
        super(ResourceStatusChangeEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(ResourceStatusChangeEmail, self).get_context_data(**kwargs)
        ctx['user'] = self.user
        ctx['recipient'] = self.recipient
        ctx['forwards'] = self.forwards
        ctx['proposed_resource'] = self.proposed_resource
        ctx['proposed_resource_url'] = get_absolute_url(
            self.proposed_resource.get_absolute_url())
        if self.proposed_resource.request:
            ctx['staffing_req_url'] = get_absolute_url(
                self.proposed_resource.request.get_absolute_url())
        ctx['project_url'] = get_absolute_url(
            self.proposed_resource.project.get_absolute_url())
        ctx['signature'] = True
        return ctx

    def render_to_message(self, *args, **kwargs):

        kwargs['to'] = (self.recipient.email,)
        kwargs['from_email'] = "{username} {email}"\
            .format(username=self.user.get_name_display(),
                    email=settings.NO_REPLY_EMAIL)
        return super(ResourceStatusChangeEmail,
                     self).render_to_message(*args, **kwargs)


class NewStaffingEmail(BaseEmailTemplateView):
    subject_template_name =\
        'projects/emails/staffing/subject.txt'
    body_template_name =\
        'projects/emails/staffing/message.txt'
    html_body_template_name =\
        'projects/emails/staffing/email.html'

    def __init__(self, user, recipient,
                 staffing_request, *args, **kwargs):
        self.user = user
        self.recipient = recipient
        self.staffing_request = staffing_request
        super(NewStaffingEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(NewStaffingEmail, self).get_context_data(**kwargs)
        ctx['user'] = self.user
        ctx['staffing_request'] = self.staffing_request
        ctx['resource_url'] = get_absolute_url(
            self.staffing_request.get_absolute_url())
        ctx['project_url'] = get_absolute_url(
            self.staffing_request.project.get_absolute_url())
        ctx['accept_url'] =\
            get_absolute_url(reverse('projects:staffing_confirmation',
                                     args=(self.staffing_request.id,
                                           RequestVendorRelationship.
                                           accepted)))

        ctx['decline_url'] =\
            get_absolute_url(reverse('projects:staffing_confirmation',
                                     args=(self.staffing_request.id,
                                           RequestVendorRelationship.
                                           rejected)))
        ctx['signature'] = True
        return ctx

    def render_to_message(self, *args, **kwargs):

        kwargs['to'] = (self.recipient.email,)
        kwargs['from_email'] = "{username} {email}"\
            .format(username=self.user.get_name_display(),
                    email=settings.NO_REPLY_EMAIL)
        return super(NewStaffingEmail,
                     self).render_to_message(*args, **kwargs)


class RequestInfoEmail(BaseEmailTemplateView):
    subject_template_name = 'projects/emails/request_info/subject.txt'
    body_template_name = 'projects/emails/request_info/message.txt'
    html_body_template_name = 'projects/emails/request_info/email.html'

    def __init__(self, user, sender, message,
                 staffing_request, *args, **kwargs):
        self.user = user
        self.staffing_request = staffing_request
        self.sender = sender
        self.message = message
        super(RequestInfoEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(RequestInfoEmail, self).get_context_data(**kwargs)
        ctx['user'] = self.user
        ctx['staffing_request'] = self.staffing_request
        ctx['sender'] = self.sender
        ctx['message'] = self.message
        ctx['resource_url'] = get_absolute_url(
            self.staffing_request.get_absolute_url())
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = (self.user.email,)
        kwargs['from_email'] = "{username} {email}"\
            .format(username=self.sender.get_name_display(),
                    email=settings.NO_REPLY_EMAIL)
        return super(RequestInfoEmail, self).render_to_message(*args,
                                                               **kwargs)


class StaffingConfirmationView(BaseEmailTemplateView):
    subject_template_name = 'projects/emails/sr_confirmation/subject.txt'
    body_template_name = 'projects/emails/sr_confirmation/message.txt'
    html_body_template_name = 'projects/emails/sr_confirmation/email.html'

    def __init__(self, user,
                 recipient,
                 vendor,
                 staffing_request,
                 confirm,
                 *args, **kwargs):

        self.user = user
        self.staffing_request = staffing_request
        self.recipient = recipient
        self.confirm = confirm
        self.vendor = vendor
        super(StaffingConfirmationView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(StaffingConfirmationView, self).get_context_data(**kwargs)
        ctx['user'] = self.user
        ctx['vendor'] = self.vendor
        ctx['staffing_request'] = self.staffing_request
        ctx['recipient'] = self.recipient
        ctx['confirm'] = self.confirm
        ctx['resource_url'] = get_absolute_url(
            self.staffing_request.get_absolute_url())
        ctx['project_url'] = get_absolute_url(
            self.staffing_request.project.get_absolute_url())
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = (self.recipient.email,)
        kwargs['from_email'] = "{vendor} {email}"\
            .format(vendor=self.vendor.name,
                    email=settings.NO_REPLY_EMAIL)
        return super(StaffingConfirmationView, self)\
            .render_to_message(*args, **kwargs)


class ShareProjectEmail(BaseEmailTemplateView):
    subject_template_name = 'projects/emails/share_project/subject.txt'
    body_template_name = 'projects/emails/share_project/message.txt'
    html_body_template_name = 'projects/emails/share_project/email.html'

    def __init__(self, user,
                 recipient,
                 project,
                 message,
                 *args, **kwargs):

        self.user = user
        self.project = project
        self.recipient = recipient
        self.message = message
        super(ShareProjectEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(ShareProjectEmail, self).get_context_data(**kwargs)
        ctx['user'] = self.user
        ctx['project'] = self.project
        ctx['recipient'] = self.recipient
        ctx['project_url'] = get_absolute_url(
            self.project.get_absolute_url())
        ctx['message'] = self.message
        ctx['signature'] = True
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = (self.recipient.email,)
        kwargs['from_email'] = "{user} {email}"\
            .format(user=self.user.get_name_display(),
                    email=settings.NO_REPLY_EMAIL)
        return super(ShareProjectEmail, self)\
            .render_to_message(*args, **kwargs)


class NewStaffingClientEmail(BaseEmailTemplateView):
    subject_template_name =\
        'projects/emails/staffing/client/subject.txt'
    body_template_name =\
        'projects/emails/staffing/client/message.txt'
    html_body_template_name =\
        'projects/emails/staffing/client/email.html'

    def __init__(self, user, recipient,
                 staffing_request, *args, **kwargs):
        self.user = user
        self.recipient = recipient
        self.staffing_request = staffing_request
        super(NewStaffingClientEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(NewStaffingClientEmail, self).get_context_data(**kwargs)
        ctx['user'] = self.user
        ctx['staffing_request'] = self.staffing_request
        ctx['resource_url'] = get_absolute_url(
            self.staffing_request.get_absolute_url())
        ctx['project_url'] = get_absolute_url(
            self.staffing_request.project.get_absolute_url())
        ctx['signature'] = True
        return ctx

    def render_to_message(self, *args, **kwargs):

        kwargs['to'] = (self.recipient.email,)
        kwargs['from_email'] = "{username} {email}"\
            .format(username=self.user.get_name_display(),
                    email=settings.NO_REPLY_EMAIL)
        return super(NewStaffingClientEmail,
                     self).render_to_message(*args, **kwargs)
