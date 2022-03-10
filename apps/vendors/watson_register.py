from watson import search as watson
from .models import Vendor

if not watson.is_registered(Vendor):
    watson.register(Vendor.objects.all(), fields=("id",
                                    "name",
                                    "summary",
                                    "locations",
                                    "categories",
                                    "roles",
                                    "portfolio__title"
                                    ))
