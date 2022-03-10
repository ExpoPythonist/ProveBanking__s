from django.db import models
from django.utils.timezone import now
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from filtered_contenttypes.fields import FilteredGenericForeignKey
from django_pgjson.fields import JsonBField

from .managers import ActionManager
from . import settings as app_settings
from . import registry


def _default_action_meta():
    return {}


class Action(models.Model):
    item_type = models.ForeignKey(ContentType, related_name='actions')
    item_id = models.PositiveIntegerField()
    item = FilteredGenericForeignKey('item_type', 'item_id')

    target_type = models.ForeignKey(ContentType, blank=True, null=True,
                                    related_name='target_actions')
    target_id = models.PositiveIntegerField(blank=True, null=True)
    target = FilteredGenericForeignKey('target_type', 'target_id')

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='activity')
    verb = models.CharField(max_length=23,
                            choices=registry.as_model_choices())
    published = models.DateTimeField(auto_now_add=True)

    meta = JsonBField(default=_default_action_meta, blank=True)

    objects = ActionManager()

    class Meta:
        abstract = app_settings.get('ACTION_MODEL') != 'simple_activity.Action'
        ordering = ('-published',)

    @classmethod
    def add_action(klass, verb, actor, item, target=None, published=None,
                      meta={}):
        if not registry.is_valid(verb):
            raise ValueError('`{}` not a valid verb.'.format(verb))
        published = published or now()
        create_kwargs = {'actor': actor, 'item': item, 'verb': verb.code}
        if target:
            create_kwargs['target'] = target
            create_kwargs['published'] = published
        klass.objects.create(**create_kwargs)

    @property
    def verb_object(self):
        return registry.get_from_code(self.verb)
