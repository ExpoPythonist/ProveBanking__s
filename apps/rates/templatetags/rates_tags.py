from django import template
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

register = template.Library()


def rate_card(user):
    return render_to_string('rates/as_field.html', {
        'rate': user.get_rate(),
        'edit_url': reverse('rates:edit_user_rate', args=(user.username,))
    })
register.filter('rate_card', rate_card)
