from django import template
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType

from ..models import Metric

register = template.Library()


def __get_review_url__(name, obj):
    ctype = ContentType.objects.get_for_model(obj)
    if not obj._meta.model in Metric._supported_models:
        raise TypeError('{} does not have support for reviews enabled. '
                        'Enable it by adding a ReviewsField() to the '
                        'model.'.format(ctype))
    return reverse('reviews:{}'.format(name), args=(ctype.id, obj.id,))


@register.assignment_tag
def assign_review_url(name, obj):
    return __get_review_url__(name, obj)


@register.simple_tag
def get_review_url(name, obj):
    return __get_review_url__(name, obj)


def get_review_class(score):
    if score is None:
        return 'secondary'
    if score <= 2.5:
        return 'danger'
    if 2.5 < score <= 4:
        return 'warning'
    if score > 4:
        return 'success'
register.simple_tag(get_review_class)

def get_review_color_class(score):
    if score is None:
        return 'secondary'
    if score <= 1.5:
        return 'one'
    if 1.5 < score <= 2.5:
        return 'two'
    if 2.5 < score <= 3.5:
        return 'three'
    if 3.5 < score <= 4.5:
        return 'four'
    if score > 4.5:
        return 'five'
register.simple_tag(get_review_color_class)
