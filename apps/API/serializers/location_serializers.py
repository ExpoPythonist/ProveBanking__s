from rest_framework import serializers

from locations.models import Location

__all__ = ('LocationSerializer',)


class LocationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='city')
    label = serializers.CharField(source='city')
    value = serializers.CharField(source='id')

    class Meta:
        model = Location
        fields = ('id', 'name', 'value', 'label')
