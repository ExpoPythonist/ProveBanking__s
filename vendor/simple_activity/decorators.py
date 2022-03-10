from django.db.models import Q
from django.contrib.auth import get_user_model

from .utils import get_action_model


def fetch_stream(self, include_secondary=True, **kwargs):
    kwargs['item'] = self
    if include_secondary:
        kwargs['target'] = self
    return get_action_model().objects.activity_stream(**kwargs)


def register_model(fetch_method='activity_stream'):
    def register(model):
        setattr(model, fetch_method, fetch_stream)
        return model
    return register
