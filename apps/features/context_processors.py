from . import registry


def features_processor(request):
    return {'features': registry.CODENAME_MAP}
