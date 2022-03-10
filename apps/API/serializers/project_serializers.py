from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers

from channels.models import Message
from projects.models import (Project, ProposedResource, StaffingRequest,
                             ProposedResourceStatus)
from .role_serializers import RoleSerializer

PRS = ProposedResourceStatus


__all__ = ('ProjectSerializer', 'ResponseSerializer',)


class StatusSerializer(serializers.ModelSerializer):
    forwards = serializers.SerializerMethodField()
    value = serializers.CharField(source='get_value_code')

    class Meta:
        model = ProposedResourceStatus
        fields = ('id', 'name', 'value', 'forwards')

    def get_forwards(self, obj):
        return obj.forwards.values('id', 'name')


class ResponseSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='get_status_value')
    role = RoleSerializer()
    #status = StatusSerializer()

    username = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    initials = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    vendor = serializers.SerializerMethodField()
    avg_score = serializers.SerializerMethodField()

    class Meta:
        model = ProposedResource
        fields = ('id', 'role', 'name', 'avatar', 'initials',
                  'vendor', 'username', 'request', 'avg_score')

    def get_avg_score(self, obj):
        return obj.resource.avg_score

    def get_username(self, obj):
        return obj.resource.username

    def get_name(self, obj):
        return obj.resource.get_name_display()

    def get_initials(self, obj):
        return obj.resource.get_initials()

    def get_avatar(self, obj):
        return obj.resource.get_avatar_url()

    def get_vendor(self, obj):
        return obj.resource.get_company_display()


class RequestSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='text_title')
    empty_positions = serializers.IntegerField(source='get_empty_positions')
    location = serializers.StringRelatedField()
    role = RoleSerializer()
    categories = serializers.StringRelatedField(many=True)
    vendors_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    users_count = serializers.SerializerMethodField()
    responses = serializers.SerializerMethodField()

    class Meta:
        model = StaffingRequest
        fields = ('id', 'title', 'empty_positions', 'role', 'location',
                  'categories', 'vendors_count', 'users_count', 'responses',
                  'comments_count')

    def get_comments_count(self, obj):
        return Message.objects.filter(
            channel__content_type=ContentType.objects.get_for_model(obj),
            channel__object_id=obj.id).count()

    def get_vendors_count(self, obj):
        return obj.vendors.count()

    def get_users_count(self, obj):
        return obj.proposed.count()

    def get_responses(self, obj):
        return ResponseSerializer(obj.proposed.all(), many=True).data


class ProjectSerializer(serializers.ModelSerializer):
    division = serializers.StringRelatedField()
    requests = RequestSerializer(many=True, source='staffing_requests',
                                 read_only=True)
    responses = serializers.SerializerMethodField(read_only=True)
    owners = serializers.StringRelatedField(many=True)

    class Meta:
        model = Project
        fields = ('id', 'division', 'title', 'start_date', 'end_date',
                  'owners', 'requests', 'responses')
        depth = 1

    def get_responses(self, obj):
        return ResponseSerializer(obj.proposals.filter(request=None), many=True).data
