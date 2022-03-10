from django.conf import settings
from django.core.urlresolvers import reverse

from med_social.libs.template import BaseEmailTemplateView
from med_social.utils import get_absolute_url, get_current_tenant

from reviews.templatetags.review_tags import get_review_url


class VendorInvitationEmail(BaseEmailTemplateView):
    subject_template_name = 'vendors/emails/invite/subject.txt'
    body_template_name = 'vendors/emails/invite/message.txt'
    html_body_template_name = 'vendors/emails/invite/email.html'

    def __init__(self, recipient, direct_url,
                 url, sender, reset_password_url, *args, **kwargs):
        self.recipient = recipient
        self.direct_url = direct_url
        self.url = url
        self.sender = sender
        self.reset_password_url = reset_password_url
        super(VendorInvitationEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(VendorInvitationEmail, self).get_context_data(**kwargs)
        ctx['recipient'] = self.recipient
        ctx['direct_url'] = self.direct_url
        ctx['url'] = self.url
        ctx['sender'] = self.sender
        ctx['reset_password_url'] = self.reset_password_url
        ctx['tenant_url'] = get_absolute_url(reverse('home'))
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = (self.recipient.email,)
        sender = (self.sender.get_name_display() if self.sender
                  else get_current_tenant().name)
        kwargs['from_email'] = "{username} {email}".format(username=sender, email=settings.NO_REPLY_EMAIL)
        return super(VendorInvitationEmail, self).render_to_message(*args, **kwargs)


class VendorApplicationEmail(BaseEmailTemplateView):
    subject_template_name = 'vendors/emails/application/subject.txt'
    body_template_name = 'vendors/emails/application/message.txt'
    html_body_template_name = 'vendors/emails/application/email.html'

    def __init__(self, vendor, *args, **kwargs):
        self.vendor = vendor
        super(VendorApplicationEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(VendorApplicationEmail, self).get_context_data(**kwargs)
        ctx['vendor'] = self.vendor
        ctx['direct_url'] = get_absolute_url(self.vendor.get_absolute_url())
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = (self.vendor.client_contact.email,)
        kwargs['from_email'] = "{username} {email}".format(username='Proven', email=settings.NO_REPLY_EMAIL)
        return super(VendorApplicationEmail, self).render_to_message(*args, **kwargs)


class ReviewRequestEmail(BaseEmailTemplateView):
    subject_template_name = 'vendors/emails/review/subject.txt'
    body_template_name = 'vendors/emails/review/message.txt'
    html_body_template_name = 'vendors/emails/review/email.html'

    def __init__(self, recipient, portfolio_item,
                 *args, **kwargs):

        self.portfolio_item = portfolio_item
        self.recipient = recipient

        super(ReviewRequestEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(ReviewRequestEmail, self).get_context_data(**kwargs)
        ctx['recipient'] = self.recipient
        ctx['portfolio_item'] = self.portfolio_item
        ctx['tenant_url'] = get_absolute_url(reverse('home'))
        ctx['review_url'] = get_absolute_url(get_review_url('add',
                                                            self.portfolio_item))
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = (self.recipient.email,)

        kwargs['from_email'] = "{vendor} {email}".format(vendor=self.portfolio_item.vendor.name,
                    email=settings.NO_REPLY_EMAIL)

        return super(ReviewRequestEmail, self).render_to_message(*args, **kwargs)


class ClientReferenceEmail(BaseEmailTemplateView):
    subject_template_name = 'vendors/public/emails/client_add/subject.txt'
    body_template_name = 'vendors/public/emails/client_add/message.txt'
    html_body_template_name = 'vendors/public/emails/client_add/email.html'

    def __init__(self, obj, *args, **kwargs):
        self.object = obj
        self.to = kwargs.pop('to', [])
        super(ClientReferenceEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(ClientReferenceEmail, self).get_context_data(**kwargs)
        ctx['object'] = self.object
        ctx['confirm_url'] = get_absolute_url(
            reverse('vendors:client_confirm', args=(self.object.vendor.id, self.object.token,))
        )
        ctx['vendor_url'] = get_absolute_url(self.object.vendor.get_absolute_url())
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = (self.object.email,) if not self.to else self.to
        kwargs['from_email'] = "{username} via Proven {email}".format(
            username=self.object.created_by.get_name_display(), email=settings.NO_REPLY_EMAIL)
        return super(ClientReferenceEmail, self).render_to_message(*args, **kwargs)


class SendMessageEmail(BaseEmailTemplateView):
    subject_template_name = 'vendors/public/emails/send_message/subject.txt'
    body_template_name = 'vendors/public/emails/send_message/message.txt'
    html_body_template_name = 'vendors/public/emails/send_message/email.html'

    def __init__(self, obj, *args, **kwargs):
        self.object = obj
        super(SendMessageEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(SendMessageEmail, self).get_context_data(**kwargs)
        ctx['object'] = self.object
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = (self.object.receiver.email,)
        kwargs['from_email'] = "{} via Proven <suzanne@proven.cc>".format(self.object.name)
        return super(SendMessageEmail, self).render_to_message(*args, **kwargs)


class VendorWelcomeEmail(BaseEmailTemplateView):
    subject_template_name = 'vendors/public/emails/vendor_welcome/subject.txt'
    body_template_name = 'vendors/public/emails/vendor_welcome/message.txt'
    html_body_template_name = 'vendors/public/emails/vendor_welcome/email.html'

    def __init__(self, obj, *args, **kwargs):
        self.object = obj
        super(VendorWelcomeEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(VendorWelcomeEmail, self).get_context_data(**kwargs)
        ctx['object'] = self.object
        ctx['user'] = self.object.users.first()
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = (self.object.email,)
        kwargs['from_email'] = "Proven <suzanne@proven.cc>"
        return super(VendorWelcomeEmail, self).render_to_message(*args, **kwargs)


class ClientRespondedEmail(BaseEmailTemplateView):
    subject_template_name = 'vendors/public/emails/client_responded/subject.txt'
    body_template_name = 'vendors/public/emails/client_responded/message.txt'
    html_body_template_name = 'vendors/public/emails/client_responded/email.html'

    def __init__(self, obj, *args, **kwargs):
        self.object = obj
        super(ClientRespondedEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(ClientRespondedEmail, self).get_context_data(**kwargs)
        ctx['object'] = self.object
        ctx['is_first_client'] = (self.object.vendor.clients.count() == 1)
        ctx['add_client_url'] = get_absolute_url(reverse('vendors:client_add', args=(self.object.vendor.id,)))
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = (self.object.created_by.email,)
        kwargs['from_email'] = "Proven <suzanne@proven.cc>"
        return super(ClientRespondedEmail, self).render_to_message(*args, **kwargs)


class VendorApprovedEmail(BaseEmailTemplateView):
    subject_template_name = 'vendors/public/emails/vendor_approved/subject.txt'
    body_template_name = 'vendors/public/emails/vendor_approved/message.txt'
    html_body_template_name = 'vendors/public/emails/vendor_approved/email.html'

    def __init__(self, obj, *args, **kwargs):
        self.object = obj
        super(VendorApprovedEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(VendorApprovedEmail, self).get_context_data(**kwargs)
        ctx['object'] = self.object
        ctx['vendor_url'] = get_absolute_url(self.object.get_absolute_url())
        ctx['clients_add_url'] = get_absolute_url(reverse('vendors:client_add', args=(self.object.id,)))
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = (self.object.email,)
        kwargs['from_email'] = "Proven <suzanne@proven.cc>"
        return super(VendorApprovedEmail, self).render_to_message(*args, **kwargs)


class CertVerificationEmail(BaseEmailTemplateView):
    subject_template_name = 'vendors/public/emails/cert_verification/subject.txt'
    body_template_name = 'vendors/public/emails/cert_verification/message.txt'
    html_body_template_name = 'vendors/public/emails/cert_verification/email.html'

    def __init__(self, obj, recipients, *args, **kwargs):
        self.object = obj
        self.recipients = recipients
        super(CertVerificationEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(CertVerificationEmail, self).get_context_data(**kwargs)
        ctx['object'] = self.object
        ctx['confirm_url'] = get_absolute_url(
            reverse(
                'vendors:cert_confirm', args=(self.object.vendor.id, self.object.token))
        )
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = self.recipients
        kwargs['from_email'] = "{username} via Proven <suzanne@proven.cc>".format(username=self.object.vendor.name)
        return super(CertVerificationEmail, self).render_to_message(*args, **kwargs)


class InsuranceVerificationEmail(BaseEmailTemplateView):
    subject_template_name = 'vendors/public/emails/insurance_verification/subject.txt'
    body_template_name = 'vendors/public/emails/insurance_verification/message.txt'
    html_body_template_name = 'vendors/public/emails/insurance_verification/email.html'

    def __init__(self, obj, recipients, *args, **kwargs):
        self.object = obj
        self.recipients = recipients
        super(InsuranceVerificationEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(InsuranceVerificationEmail, self).get_context_data(**kwargs)
        ctx['object'] = self.object
        ctx['confirm_url'] = get_absolute_url(
            reverse('vendors:insurance_confirm', args=(self.object.vendor.id, self.object.token))
        )
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = self.recipients
        kwargs['from_email'] = "{username} via Proven <suzanne@proven.cc>".format(username=self.object.vendor.name)
        return super(InsuranceVerificationEmail, self).render_to_message(*args, **kwargs)


class ClientVendorRelEmail(BaseEmailTemplateView):
    subject_template_name = 'vendors/public/emails/partner_verification/subject.txt'
    body_template_name = 'vendors/public/emails/partner_verification/message.txt'
    html_body_template_name = 'vendors/public/emails/partner_verification/email.html'

    def __init__(self, obj, recipients, *args, **kwargs):
        self.object = obj
        self.recipients = recipients
        super(ClientVendorRelEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(ClientVendorRelEmail, self).get_context_data(**kwargs)
        ctx['object'] = self.object
        ctx['confirm_url'] = get_absolute_url(
            reverse(
                'vendors:partner_confirm',
                args=(self.object.vendor.id, self.object.token))
        )
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = self.recipients
        kwargs['from_email'] = "{username} via Proven <suzanne@proven.cc>".format(username=self.object.vendor.name)
        return super(ClientVendorRelEmail, self).render_to_message(*args, **kwargs)


class ClientConfirmedEmail(BaseEmailTemplateView):
    subject_template_name = 'vendors/public/emails/client_vendor_rel_confirm/subject.txt'
    body_template_name = 'vendors/public/emails/client_vendor_rel_confirm/message.txt'
    html_body_template_name = 'vendors/public/emails/client_vendor_rel_confirm/email.html'

    def __init__(self, obj, *args, **kwargs):
        self.object = obj
        self.recipient = obj.vendor.email
        super(ClientConfirmedEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(ClientConfirmedEmail, self).get_context_data(**kwargs)
        ctx['object'] = self.object
        ctx['profile_url'] = get_absolute_url(
            reverse(
                'vendors:edit_profile',
                args=(self.object.vendor.id,))
        )
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = (self.recipient, )
        kwargs['from_email'] = "{username} via Proven <suzanne@proven.cc>".format(username=self.object.client.name)
        return super(ClientConfirmedEmail, self).render_to_message(*args, **kwargs)


class ProcurementNotifyEmail(BaseEmailTemplateView):
    subject_template_name = 'vendors/emails/procurement/vendor_update/subject.txt'
    body_template_name = 'vendors/emails/procurement/vendor_update/message.txt'
    html_body_template_name = 'vendors/emails/procurement/vendor_update/email.html'

    def __init__(self, recipient, vendor, *args, **kwargs):
        self.vendor = vendor
        self.recipient = recipient
        super(ProcurementNotifyEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(ProcurementNotifyEmail, self).get_context_data(**kwargs)
        ctx['vendor'] = self.vendor
        ctx['profile_url'] = self.vendor.get_absolute_url()
        ctx['recipient'] = self.recipient
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = (self.recipient.email, )
        kwargs['from_email'] = "{username} via Proven <noreply@proven.cc>".format(username=self.vendor.name)
        return super(ProcurementNotifyEmail, self).render_to_message(*args, **kwargs)


class ProcurementAddedEmail(BaseEmailTemplateView):
    subject_template_name = 'vendors/emails/procurement/add/subject.txt'
    body_template_name = 'vendors/emails/procurement/add/message.txt'
    html_body_template_name = 'vendors/emails/procurement/add/email.html'

    def __init__(self, recipient, vendor, *args, **kwargs):
        self.vendor = vendor
        self.recipient = recipient
        super(ProcurementAddedEmail, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(ProcurementAddedEmail, self).get_context_data(**kwargs)
        ctx['vendor'] = self.vendor
        ctx['profile_url'] = self.vendor.get_absolute_url()
        ctx['recipient'] = self.recipient
        return ctx

    def render_to_message(self, *args, **kwargs):
        kwargs['to'] = (self.recipient.email, )
        kwargs['from_email'] = "{username} via Proven <noreply@proven.cc>".format(username=self.vendor.name)
        return super(ProcurementAddedEmail, self).render_to_message(*args, **kwargs)
