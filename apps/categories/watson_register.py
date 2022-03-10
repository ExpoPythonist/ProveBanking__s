from watson import search as watson
from .models import Category

if not watson.is_registered(Category):
    watson.register(Category.objects.all(),
                    fields=("id", "name",))
