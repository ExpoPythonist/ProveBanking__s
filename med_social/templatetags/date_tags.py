from datetime import date

from django import template

from med_social.utils import humanized_date, this_month


register = template.Library()


@register.filter
def natural_date(date):
    return humanized_date(date)


@register.filter(name='as_month_name')
def as_month_name(month_number, format_string='%b'):
    return date(2000, month_number, 1).strftime(format_string)


@register.simple_tag(name='month_range_as_format')
def month_range_as_format(month_number, format_string='%b'):
    start = this_month().month
    end = this_month().month + month_number
    return '{} - {}'.format(
        date(2000, start, 1).strftime(format_string),
        date(2000, end, 1).strftime(format_string)
    )
