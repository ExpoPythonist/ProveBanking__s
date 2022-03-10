from watson import search as watson

from django.contrib.auth import get_user_model

user = get_user_model()
if not watson.is_registered(user):
    watson.register(user.objects.all(), fields=("first_name", "last_name", "username", "bio", "location", "vendor"))
