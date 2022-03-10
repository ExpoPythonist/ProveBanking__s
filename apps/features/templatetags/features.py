from django import template


register = template.Library()


@register.filter
def is_feature_enabled(feature, tenant=None):
    return feature.is_enabled(tenant)
