from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def militarytime(time, separator=':'):
    """Converts simple AM/PM time strings from 12 hr to 24hr format
    Example
        input: 9:30 pm
        output: 2130
    Does not handle 
    """

    if time is None:
        return '0000'
    elif time.lower().endswith('am'):
        hours, minutes = time.lower().rstrip('am').strip().split(':')
    elif time.lower().endswith('pm'):
        hours, minutes = time.lower().rstrip('pm').strip().split(':')
        hours = int(hours) + 12
    else:
        return '0000'
    return "%02d%s%s" % (hours, separator, minutes)

@register.filter
def to12hrs(militarytime, pad=False):
    """Convert simple military time string to AM/PM format
    Example:
        input: 2130
        output: 9:30 pm
    """
    hours = int(militarytime[0:2])
    minutes = int(militarytime[2:])
    meridiem = ''
    formater = '%d:%02d %s'

    if hours > 12:
        hours = hours - 12
        meridiem = 'pm'
    elif hours < 12:
        meridiem = 'am'

    if pad:
        formater = '%02d:%02d %s'

    return formater % (hours, minutes, meridiem)
