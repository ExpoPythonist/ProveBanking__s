from rest_framework import serializers

from certs.models import Cert


__all__ = ('CertSerializer',)


class CertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cert
        fields = ('id', 'name', 'kind',)
 