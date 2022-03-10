from .types import Feature

REGISTRY = {}
CODENAME_MAP = {}


def register(id, codename, title, description):
    feature = Feature(id, codename=codename, title=title, description=description)
    REGISTRY[id] = feature
    CODENAME_MAP[codename] = feature
    return feature



