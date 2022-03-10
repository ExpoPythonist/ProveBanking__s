from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from availability.models import Week
from med_social.utils import this_week
from ..fields import Base64FileField


__all__ = ('UserSerializer',)


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='get_name_display', read_only=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    initials = serializers.CharField(source='get_initials', read_only=True)
    avatar = serializers.URLField(source='get_avatar_url', read_only=True)
    vendor = serializers.StringRelatedField()
    label = serializers.CharField(source='get_name_display', read_only=True)
    value = serializers.CharField(source='id', read_only=True)
    is_client = serializers.BooleanField(read_only=True)
    email = serializers.CharField(write_only=True, validators=[
        UniqueValidator(queryset=get_user_model().objects.all(),
                        message='A user with that email already exists')])
    username = serializers.CharField(required=False, allow_blank=True)
    linkedin_profile_url = serializers.URLField(required=False, allow_blank=True)
    resume = Base64FileField(required=False, allow_empty_file=False, use_url=True)

    class Meta:
        model = get_user_model()
        fields = ('id', 'name', 'first_name', 'last_name', 'username',
                  'avatar', 'initials', 'vendor', 'avg_score', 'label',
                  'value', 'is_client', 'email', 'linkedin_profile_url',
                  'resume')
        read_only_fields = ('avg_score',)
