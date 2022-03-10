from annoying.functions import get_object_or_None
from .models import SEOMetadata


def seo_metadata(request):
    metadata = get_object_or_None(SEOMetadata, path=request.path)
    if metadata:
        return {'metadata': metadata}
    return {}
