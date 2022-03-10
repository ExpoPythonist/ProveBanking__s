from django.contrib.auth import get_user_model
from rest_framework import serializers

from projects.models import Project, ProposedResource, StaffingRequest
from .role_serializers import RoleSerializer


__all__ = ('ProposedUserSerializer',)


class ProposedSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='get_status_value')
    role = RoleSerializer()

    class Meta:
        model = ProposedResource
        fields = ('id', 'resource', 'status', 'role')


class RequestSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='text_title')
    empty_positions = serializers.IntegerField(source='get_empty_positions')
    location = serializers.StringRelatedField()
    role = RoleSerializer()

    class Meta:
        model = StaffingRequest
        fields = ('id', 'title', 'empty_positions', 'role', 'location')


class ProposedUserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='get_name_display')
    initials = serializers.CharField(source='get_initials')
    avatar = serializers.URLField(source='get_avatar_url')
    vendor = serializers.StringRelatedField()
    proposed = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ('id', 'name', 'username', 'avatar', 'initials', 'vendor', 'proposed')

    def get_proposed(self, obj):
        return ProposedSerializer(obj.proposed.filter(
            project=self.context['view'].kwargs['project_pk']),
            many=True
        ).data
