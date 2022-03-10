import re
import json

from django.db import connection
from django.conf import settings
from django import forms
from django.shortcuts import render_to_response
from django.contrib.auth import get_user_model
from django.template import RequestContext
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.core.mail.message import EmailMultiAlternatives, EmailMessage

from allauth.exceptions import ImmediateHttpResponse
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import get_adapter as get_account_adapter
from annoying.functions import get_object_or_None

from users.models import User


class AccountAdapter(DefaultAccountAdapter):

    def is_open_for_signup(self, request):
        """
        Checks whether or not the site is open for signups.

        Next to simply returning True/False you can also intervene the
        regular flow by raising an ImmediateHttpResponse
        """
        # @todo change public schema_name to a setting constant
        if connection.schema_name == 'public':
            return True
        else:
            if Team.objects.exists():
                return True
            else:
                return False

    def generate_unique_username(self, txts, regex=None):
        regex = settings.ACCOUNT_USERNAME_REGEX
        return super(AccountAdapter, self).generate_unique_username(txts, regex)

    def get_login_redirect_url(self, request):
        return request.GET.get('next') or super(AccountAdapter, self).get_login_redirect_url(request)

    def clean_password(self, password):
        password = super(AccountAdapter, self).clean_password(password)
        if not re.match(settings.ACCOUNT_PASSWORD_REGEX, password):
            raise forms.ValidationError('Password must contain at least 1 upper case, 1 lower case and a digit.')
        return password

    def send_mail(self, template_prefix, email, context):
        """
        Sends an e-mail to `email`.  `template_prefix` identifies the
        e-mail that is to be sent, e.g. "account/email/email_confirmation"
        """
        subject = render_to_string('{0}_subject.txt'.format(template_prefix), context)
        # remove superfluous line breaks
        subject = " ".join(subject.splitlines()).strip()
        subject = self.format_email_subject(subject)

        bodies = {}
        for ext in ['html', 'txt']:
            try:
                template_name = '{0}_message.{1}'.format(template_prefix, ext)
                bodies[ext] = render_to_string(template_name, context).strip()
            except TemplateDoesNotExist:
                if ext == 'txt' and not bodies:
                    # We need at least one body
                    raise
        if 'txt' in bodies:
            msg = EmailMultiAlternatives(subject, bodies['txt'], settings.DEFAULT_FROM_EMAIL, [email])
            if 'html' in bodies:
                msg.attach_alternative(bodies['html'], 'text/html')
        else:
            msg = EmailMessage(subject, bodies['html'], settings.DEFAULT_FROM_EMAIL, [email])
            msg.content_subtype = 'html'  # Main content is now text/html

        msg.send()
