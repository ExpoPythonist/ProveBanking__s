from django.db import models
from djorm_pguuid.fields import UUIDField


class UUIDPrimaryKeyMixin():
    id = UUIDField(auto_add=True, primary_key=True)


class TimestampedModelMixin():
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
