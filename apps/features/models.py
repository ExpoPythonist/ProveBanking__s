from . import registry
from .exceptions import FeatureNotDefined, FeatureAlreadyRegistered


def get_by_id(id):
    if id in registry.REGISTRY:
        return registry.REGISTRY[id]
    else:
        raise FeatureNotDefined()


def get_by_id_or_None(id):
    try:
        get_by_id(id)
    except FeatureNotDefined:
        return None


def get_by_codename(codename):
    if codename in registry.CODENAME_MAP:
        return registry.CODENAME_MAP[codename]
    else:
        raise FeatureNotDefined()


def get_by_codename_or_None(codename):
    try:
        get_by_codename(codename)
    except FeatureNotDefined:
        return None


def get_all():
    return registry.REGISTRY.values()


def register(id, codename, title, description):
    if get_by_id_or_None(id) or get_by_codename_or_None(codename):
        raise FeatureAlreadyRegistered()
    else:
        return registry.register(id, codename, title, description)
