from django import template

register = template.Library()


@register.filter(name='as_css_class')
def get_availability_class(week):
    if week.user.next_available:
        default = 'success'
    else:
        default = 'default'

    availability = week.allocation
    if not availability:
        return default
    elif availability >= 80:
        return 'danger'
    elif 20 <= availability < 80:
        return 'warning'
    else:
        return default
