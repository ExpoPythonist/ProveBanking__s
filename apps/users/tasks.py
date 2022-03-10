from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model

from annoying.functions import get_object_or_None

from django_atomic_celery import task
from tenant_schemas.utils import tenant_context, get_tenant_model
from post_office import mail

from med_social.utils import get_absolute_url as abs_url

from .emails.views import UserInvitationEmail, UserSignupEmail


@task
def user_invite(tenant_id, invite_id, password, message=None):
    from users.models import UserInvitation
    tenant = get_object_or_None(get_tenant_model(), id=tenant_id)
    if not tenant:
        return

    with tenant_context(tenant):
        invite = get_object_or_None(UserInvitation, id=invite_id)
        if not invite:
            return
        url = ''.join([settings.DEFAULT_HTTP_PROTOCOL, tenant.domain_url])

        '''
        UserInvitationEmail(username=invite.receiver.username,
                            recipient=invite.receiver.email,
                            password=password,
                            direct_url=''.join([url,
                                                invite.get_absolute_url()]),
                            url=url,
                            sender=invite.sender,
                            reset_password_url=reverse(
                                'account_change_password'),
                            message=message,
                            ).send()
        '''
        mail.send(invite.receiver.email, template='New Community Manager', context={
            'receiver': invite.receiver,
            'direct_url': ''.join([url, invite.get_absolute_url()]),
        })



@task
def first_time_login_task(user_id, tenant_id):
    tenant = get_object_or_None(get_tenant_model(), id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        user = get_object_or_None(get_user_model(), id=user_id)
        if not user:
            return

        user.send_first_login_notification(recipients=user.invited_by.all())


@task
def signup_task(token_id, tenant_id):
    from users.models import SignupToken

    tenant = get_object_or_None(get_tenant_model(), id=tenant_id)

    if not tenant:
        return

    with tenant_context(tenant):
        token_obj = get_object_or_None(SignupToken, id=token_id)
        if not tenant.direct_signup and not token_obj.is_invited and not token_obj.is_approved:
            mail.send(
                settings.SIGNUP_REVIEWERS,
                template='User Signup Review', context={'token': token_obj, 'current_tenant': tenant},
            )
        else:
            url = ''.join([settings.DEFAULT_HTTP_PROTOCOL, tenant.domain_url])
            mail.send(token_obj.email, template='User Signup', context={
                'direct_url': ''.join([url, token_obj.get_confirm_url()]),
                'current_tenant': tenant,
            })
            '''
            UserSignupEmail(recipient=token_obj.email,
                            direct_url=''.join([url,
                                                token_obj.get_confirm_url()]),
                            ).send()
            '''
