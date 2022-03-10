from itertools import chain

from django import forms
from django.utils.safestring import mark_safe

from .utils import clean_range, prepare_range, render_stars, render_nps


class StarRatingInput(forms.Select):

    def __init__(self, *args, **kwargs):
        self.render_func = render_stars
        kwargs.pop('coerce', None)
        kwargs.pop('empty_value', None)
        super(StarRatingInput, self).__init__(*args, **kwargs)
        self.attrs['data-selectize'] = 'no'
        self.attrs['ignore-labelinplace'] = 'yes'

    def render(self, name, value, attrs=None, choices=()):
        attrs = attrs or {}
        attrs['class'] = attrs.get('class', '') + ' hide'
        attrs['data-selectize'] = 'no'
        output = super(StarRatingInput, self).render(name, value, attrs,
                                                     choices)
        star_widget = self.render_items(choices, [value],
                                        attrs.get('id', None))
        return mark_safe('\n'.join([output, star_widget]))

    def render_items(self, choices, selected, id):
        choices = chain(self.choices, choices)
        return '<div class="form-control">{0}</div>'.format(
            self.render_func(choices, selected, id))


class NPSInput(StarRatingInput):

    def __init__(self, *args, **kwargs):
        kwargs['coerce'] = int
        super(NPSInput, self).__init__(*args, **kwargs)
        self.render_func = render_nps
        self.attrs['data-selectize'] = 'no'
        self.attrs['ignore-labelinplace'] = 'yes'


class NPSField(forms.TypedChoiceField):
    widget = NPSInput

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = [(i, i) for i in range(0, 11)]
        kwargs['empty_value'] = 0
        super(NPSField, self).__init__(*args, **kwargs)

    def clean(self, value):
        value = super(NPSField, self).clean(value)
        value = float(value) / 2.0
        return value


class ReviewRatingFormField(forms.ChoiceField):
    widget = StarRatingInput


class RangeFormField(forms.CharField):
    regex = '\d+'
    css_classes = 'range-input'
    field_feedback = ''

    def __init__(self, *args, **kwargs):
        super(RangeFormField, self).__init__(*args, **kwargs)
        self.is_metric_range_field = True
        self.widget.attrs['class'] = self.widget.attrs.get(
            'class', '') + self.css_classes
        self.widget.attrs['data-field-type'] = 'range-input'
        self.widget.attrs['data-range-type'] = 'int'
        self.widget.attrs['ignore-labelinplace'] = 'true'
        if self.field_feedback:
            self.widget.attrs['data-field-feedback'] = self.field_feedback

    def prepare_value(self, value):
        return prepare_range(value)

    def clean(self, value):
        "Range represented by a list of 2 items"
        if not isinstance(value, basestring):
            return value
        value = value.strip()
        value = super(RangeFormField, self).clean(value)
        return clean_range(value, self.regex)


class DayRangeFormField(RangeFormField):
    css_classes = 'range-input'
    field_feedback = 'days'


class MonthRangeFormField(RangeFormField):
    css_classes = 'range-input'
    field_feedback = 'months'


class YearRangeFormField(RangeFormField):
    css_classes = 'range-input'
    field_feedback = 'years'
