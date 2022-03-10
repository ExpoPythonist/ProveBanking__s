from django.conf import settings

SIMPLE_ACTIVITY = {
    'ACTION_MODEL': 'simple_activity.Action'
}

SIMPLE_ACTIVITY.update(getattr(settings, 'SIMPLE_ACTIVITY', {}))


def get(name):
    return SIMPLE_ACTIVITY.get(name)
