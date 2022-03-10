from django import template
from django.forms.widgets import RadioSelect

register = template.Library()


@register.filter
def is_inline_group_field(field):
    return 'form-group-inline' in field.field.widget.attrs.get('class', '')


@register.filter
def is_selectize(field):
    return 'yes' == field.field.widget.build_attrs().get('data-selectize', '')


@register.filter
def is_radio(field):
    return isinstance(field.field.widget, RadioSelect)


@register.filter
def is_selected_choice(choice, data):
    return str(choice) in [str(d) for d in data]
