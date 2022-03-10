import datetime
from med_social.utils import days_in_date_range
from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()


@register.filter
def can_edit_profile(user, current_user):
    if user == current_user:
        return True
    if user.vendor != current_user.vendor:
        return False
    if not user.has_joined and current_user.has_perm('users.invite_user'):
        return True
