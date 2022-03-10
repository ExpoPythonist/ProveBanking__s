from mailviews.previews import Preview, site
from .views import RequestUpdateEmail

from .forms import RequestUpdatePreviewForm


# Define a new preview class.
class BasicPreview(Preview):
    message_view = RequestUpdateEmail
    form_class = RequestUpdatePreviewForm


# Register the preview class with the preview index.
site.register(BasicPreview)
