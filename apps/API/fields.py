import base64
import re

from django.core.files.base import ContentFile

from rest_framework import serializers


class JSONField(serializers.Field):
    def to_internal_value(self, obj):
        return obj

    def to_representation(self, value):
        return value


class Base64FileField(serializers.FileField):
    """
    A field to handle Base64 encoded files. Expects a dict:
        {
            name: "filename.png",
            content: "base64 encoded string"
        }
    """

    def to_internal_value(self, data):
        try:
            file_data = re.sub(r"^data\:.+base64\,(.+)$", r"\1", data["content"])
            decoded = base64.b64decode(file_data)
        except TypeError:
            raise serializers.ValidationError('Not a valid file')

        content_file = ContentFile(decoded, name=data["name"])
        return super(Base64FileField, self).to_internal_value(content_file)
