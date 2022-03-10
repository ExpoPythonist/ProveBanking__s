import re

from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe


def render_stars(choices, selected, _id, readonly=False):
    readonly = 'true' if readonly else 'false'
    output = '<ul href="#{0}" class="star-rating-input" data-readonly="{1}">'.format(_id, readonly)
    for choice in choices:
        css_class = 'selected' if choice[0] in selected else ''
        output += ('<li value="{0}"  data-toggle="tooltip" class="star-choice star-choice-{0} {2}"'
        ' title="{1}"></li>'.format(choice[0], choice[1], css_class))
    output += '</ul>'
    return mark_safe(output)


def render_nps(choices, selected, _id, readonly=False):
    readonly = 'true' if readonly else 'false'
    #output = ('<span class="text-muted">How likely are you to recommend the'
    #          ' vendor to someone a friend or colleague?</span>')
    output = '<div class="btn-toolbar ">'
    output += ('<div href="#{0}" class="btn-group btn-group-justified nps-input" role="toolbar" '
               'data-readonly="{1}">').format(_id, readonly)
    for choice in choices:
        css_class = 'active' if str(choice[0]) in selected else ''
        output += (('<div class="btn-group nps-{0} nps-field" role="group"><div class="btn btn-default nps-choice '
                    'nps-choice-{0} {2}" value="{0}" title="{1}">{0}</div></div>'
                    ).format(choice[0], choice[1], css_class))
    output += '</div></div><div class="row text-muted nps-label"><div class="col-xs-4 text-left">not likely</div><div class="col-xs-4 text-center">neutral</div><div class="col-xs-4 text-right">highly likely</div>'
    return mark_safe(output)


def prepare_range(value, unit=None):
    def return_it(value, unit):
        if unit:
            return '{} {}'.format(value, unit)
        else:
            return value

    if isinstance(value, basestring):
        return return_it(value, unit)
    if not value:
        return return_it(value, unit)
    if (value[0] and value[1]) is not None:
        return return_it('{} - {}'.format(*value), unit)
    elif value[0] is None:
        return return_it('0 - {}'.format(value[1]), unit)
    elif value[1] is None:
        return return_it('{} - {}'.format(value[0], value[1] + 100), unit)


def clean_range(value, regex='\d+'):
    "Range represented by a list of 2 items"
    #cleaned = clean_low_high(value, regex) or clean_low(value, regex) or\
    #    clean_high(value, regex)
    cleaned = clean_low_high(value, regex)
    if not cleaned:
        raise ValidationError("Range should be specified as '10 to 20'")
    return cleaned


def clean_low_high(value, regex):
    match = re.match('^(?P<low>{regex})\s*-\s*(?P<high>{regex})$'.format(
        regex=regex), value)
    if match:
        groupdict = match.groupdict()
        low = int(groupdict['low'])
        high = int(groupdict['high'])

        if low and high:
            if low > high:
                #low, high = high, low
                raise ValidationError("Lower bound cannot be greater than"
                                      " upper bound")
        if low == high:
            raise ValidationError("Range values cannot be equal")

        return (low, high)


def clean_low(value, regex):
    match = re.match('^(?P<low>{regex})\s*>\s*$'.format(
        regex=regex), value)
    if match:
        groupdict = match.groupdict()
        return (int(groupdict['low']), None,)


def clean_high(value, regex):
    match = re.match('^\s*<\s*(?P<high>{regex})$'.format(regex=regex),
                     value)
    if match:
        groupdict = match.groupdict()
        return (None, int(groupdict['high']),)
