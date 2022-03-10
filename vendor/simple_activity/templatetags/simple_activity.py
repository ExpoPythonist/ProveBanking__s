from django import template
from django.template.loader import render_to_string


register = template.Library()


@register.simple_tag(takes_context=True)
def render_action(context, action):
    context['action'] = action
    return render_to_string(action.verb_object.template_name, context)
