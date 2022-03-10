from django.conf import settings

from rest_framework import serializers

from clients.models import Client


__all__ = ('ClientSerializer',)


class ClientSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    industries = serializers.SerializerMethodField()
    is_editable = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ('id', 'name', 'logo', 'size', 'industries', 'created_by',
                  'is_editable')

    def get_logo(self, obj):
        return (obj.logo.url if obj.logo else
                settings.STATIC_URL + 'images/defaults/placeholder-co.png')

    def get_size(self, obj):
        return dict(Client.SIZE_CHOICES)[obj.size] if obj.size else None

    def get_industries(self, obj):
        return map(lambda x: x.name, obj.industries.all())

    def get_is_editable(self, obj):
        request = self.context.get('request')
        if request and obj.is_editable(request.user):
            return True
        return False
    