from django.db import models
from django.db.models import Q

from chainablemanager.manager import ChainableManager


class ActionManager(ChainableManager):
    class QuerySetMixin(object):
        def activity_stream(self, actor=None, item=None, target=None, verbs=None):
            verbs = verbs or []
            q = Q()
            if actor:
                q = q | Q(actor=actor)

            if item:
                q = q | Q(item=item)

            if actor:
                q = q | Q(target=target)

            if verbs:
                q = q | Q(verb__in=verbs)
            return self.filter(q)


def register_method(name):
    def register(method):
        setattr(ActionManager.QuerySetMixin, name, method)
        return method
    return register
