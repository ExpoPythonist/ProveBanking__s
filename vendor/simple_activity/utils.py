from django.apps import apps as django_apps
from django.core.exceptions import ImproperlyConfigured

from . import settings


def get_action_model():
    action_model = settings.get('ACTION_MODEL')

    try:
        return django_apps.get_model(action_model)
    except ValueError:
        raise ImproperlyConfigured("ACTIVITY_MODEL (in SIMPLE_ACTIVITY) must "
                                   "be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            "AUTH_USER_MODEL (in SIMPLE_ACTIVITY) refers to model '%s' "
            "that has not been installed" % action_model)
