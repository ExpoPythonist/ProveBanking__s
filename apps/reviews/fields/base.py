from django import forms
from django.forms import ValidationError
from django.utils.safestring import mark_safe

from .formfields import (ReviewRatingFormField, RangeFormField,
                         DayRangeFormField, MonthRangeFormField,
                         YearRangeFormField, NPSField)
from .utils import prepare_range, render_stars, render_nps


class BaseField(object):
    ID = 'base'
    weight = 1
    name = 'Base field'
    form_field_class = forms.CharField
    review_form_field_class = forms.ChoiceField
    editable = True
    is_core_metric = False
    default_help_text = ''
    ORDER_ASC = 1
    ORDER_DESC = 2

    ORDER_CHOICES = (
        (ORDER_ASC, 'Ascending',),
        (ORDER_DESC, 'Descending',),
    )

    _metric_data = {
        'labels': {
            '1': 'Poor',
            '2': 'Fair',
            '3': 'Good',
            '4': 'Very good',
            '5': 'Excellent',
        },
        'order': ORDER_ASC,
    }

    def __init__(self, model):
        self.model = model

    @classmethod
    def get_metric_data(self):
        return self._metric_data

    @classmethod
    def get_labels(self):
        return self._metric_data['labels']

    @classmethod
    def get_order(self):
        return self._metric_data['order']

    @classmethod
    def get_form_field_class(self):
        return self.form_field_class

    def coerce_to_key(self, score):
        return str(int(round(float(score))))

    def get_score_display(self, score):
        return self._metric_data['labels'][self.coerce_to_key(score)]

    def clean(self, value):
        return value

    def as_form_choice(self, item):
        return item

    def calculate_auto_score(self, value, labels):
        return None


class RatingField(BaseField):
    ID = 'rating'
    weight = 0
    name = 'Rating (1 - 5 stars)'
    form_field_class = forms.CharField
    review_form_field_class = ReviewRatingFormField

    def get_score_display(self, score):
        score = self.coerce_to_key(score)
        return render_stars(sorted(self._metric_data['labels'].items()),
                            [score], _id='rating',
                            readonly=True)


class IntField(BaseField):
    ID = 'int'
    name = 'Numeric'

    _metric_data = {
        'labels': {
            '1': 1,
            '2': 2,
            '3': 3,
            '4': 4,
            '5': 5,
        },
        'order': BaseField.ORDER_ASC,
    }


class NPSField(IntField):
    ID = 'nps'
    name = 'Net Promoter Score'
    review_form_field_class = NPSField
    editable = False
    default_help_text = 'How likely is it that you would recommend this'\
        ' to a friend or colleague?'

    _metric_data = {
        'labels': {
            '1': 1,
            '2': 2,
            '3': 3,
            '4': 4,
            '5': 5,
        },
        'order': BaseField.ORDER_ASC,
    }

    def coerce_to_key(self, score):
        return str(int(round(float(score) * 2)))

    def get_score_display(self, score):
        score = self.coerce_to_key(score)
        return render_nps([(str(i),i) for i in range(0, 11)],
                          [score], _id='rating', readonly=True)


class BaseRangeField(BaseField):
    ID = 'base-range'
    name = 'Range'
    form_field_class = RangeFormField
    unit = ''

    _metric_data = {
        'labels': {
            '1': [0, 5],
            '2': [5, 10],
            '3': [10, 15],
            '4': [15, 20],
            '5': [20, 30],
        },
        'order': BaseField.ORDER_ASC,
    }

    def as_form_choice(self, item):
        key, value = item
        return (key, prepare_range(value, self.unit))

    def get_score_display(self, score):
        score = self.coerce_to_key(score)
        _range = prepare_range(self._metric_data['labels'][score])
        return mark_safe(
            '{0} {1} <span class="text-muted">({2}/5)</span>'.format(
                _range, self.unit, score))

    def clean(self, value):
        if len(value) != 2:
            raise ValidationError('Range can only have 2 points')
        return value


class IntRangeField(BaseRangeField):
    ID = 'int-range'
    name = 'Numeric range'

    def clean(self, value):
        value = super(IntRangeField, self).clean(value)
        for i in value:
            if (i is not None) and (not isinstance(i, int)):
                raise ValidationError('Int range can only takes None and '
                                      'whole numbers.')
        return value


class DayRangeField(IntRangeField):
    ID = 'date-field'
    name = 'Day range'
    unit = 'days'
    form_field_class = DayRangeFormField

    _metric_data = {
        'labels': {
            '1': [0, 7],
            '2': [8, 15],
            '3': [16, 30],
            '4': [31, 50],
            '5': [51, 60],
        },
        'order': BaseField.ORDER_ASC,
    }


class ResponsivenessField(DayRangeField):
    ID = 'responsiveness-field'
    name = 'Responsiveness (Automatically calculated - time taken to propose resources)'
    unit = 'days'
    is_core_metric = True

    def calculate_auto_score(self, value, labels):
        value = value.days
        for score, _range in self.get_labels().items():
            low, high = _range
            if (low and high) and (low < value <= high):
                return score
            elif low and not high:
                if low < value:
                    return score
            elif high and not low:
                if value < high:
                    return score


class MonthRangeField(IntRangeField):
    ID = 'month-field'
    name = 'Month range'
    unit = 'months'
    form_field_class = MonthRangeFormField

    _metric_data = {
        'labels': {
            '1': [0, 1],
            '2': [2, 3],
            '3': [4, 6],
            '4': [6, 8],
            '5': [8, 12],
        },
        'order': BaseField.ORDER_ASC,
    }


class YearRangeField(IntRangeField):
    ID = 'year-field'
    name = 'Year range'
    unit = 'years'
    form_field_class = YearRangeFormField

    _metric_data = {
        'labels': {
            '1': [0, 1],
            '2': [2, 3],
            '3': [4, 5],
            '4': [6, 7],
            '5': [8, 9],
        },
        'order': BaseField.ORDER_ASC,
    }


#FIELDS = [RatingField, NPSField, IntRangeField, DayRangeField, MonthRangeField,
#          YearRangeField, ResponsivenessField,]

FIELDS = [RatingField, NPSField]
