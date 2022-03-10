from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework import serializers
from sorl.thumbnail import get_thumbnail

from vendors.models import Vendor, VendorWhois
from user_serializers import UserSerializer


__all__ = ('VendorSerializer',)


class VendorSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='id', read_only=True)
    label = serializers.CharField(source='name', read_only=True)
    logo = serializers.SerializerMethodField()
    whois = serializers.SerializerMethodField()
    verifications = serializers.SerializerMethodField()
    contacts = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = ('id', 'name', 'avg_score', 'email', 'value', 'label',
                  'logo', 'whois', 'verifications', 'contacts')

    def get_logo(self, obj):
        if obj.logo:
            return get_thumbnail(obj.logo, '100x100').url
        else:
            return settings.STATIC_URL + 'images/defaults/placeholder-co.png'

    def get_whois(self, obj):
        try:
            return VendorWhoisSerializer(obj.whois).data
        except:
            return None

    def get_verifications(self, obj):
        return obj.verifications

    def get_contacts(self, obj):
        qs = obj.contacts.all() | get_user_model().objects.filter(email=obj.email)
        return UserSerializer(qs.distinct(), many=True).data


class VendorWhoisSerializer(serializers.ModelSerializer):
    metrics = serializers.SerializerMethodField()
    social_handles = serializers.SerializerMethodField()

    class Meta:
        model = VendorWhois
        fields = ('domain', 'phone', 'address', 'email', 'registrant', 'created_on',
                  'expires_on', 'social_handles', 'metrics')

    def get_metrics(self, obj):
        return obj.metrics

    def get_social_handles(self, obj):
        return obj.social_handles
