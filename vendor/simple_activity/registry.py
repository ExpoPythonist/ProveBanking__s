from .verbs import BaseVerb
from .utils import get_action_model


_verbs = {}

def register(verb):
    if not issubclass(verb, BaseVerb):
        raise TypeError('Verb `{}` is not an instance of '
                        'activity.verbs.BaseVerb'.format(verb))
    if verb.code in _verbs.keys():
        raise ValueError('Verb `{}` is already registered'.format(verb.code))
    _verbs[verb.code] = verb

    Action = get_action_model()
    method_name = 'add_action_{}'.format(verb.code)

    def create(klass, *args, **kwargs):
        if 'verb' in kwargs:
            raise ValueError('{} does not accept `verb` as an '
                             'argument'.format(method_name))
        klass.add_action(verb, *args, **kwargs)

    setattr(Action, method_name, classmethod(create))


def as_model_choices():
    return [(V, V.capitalize()) for V in _verbs.keys()]


def get_all():
    return _verbs.values()


def get_from_code(code):
    return _verbs[code]


def is_valid(verb):
    if not issubclass(verb, BaseVerb):
        raise TypeError('`{}` is not a valid verb.'.format(verb))

    if not verb.code in _verbs:
        raise ValueError('`{}` is not a registered verb.'.format(verb))

    return True

