from rest_framework import serializers

from projects.models import StaffingRequest, RequestVendorRelationship, Project

from .role_serializers import RoleSerializer

__all__ = ('RequestSerializer', 'LeanRequestSerializer',)

class UltraLeanProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ('id', 'title',)


class LeanRequestSerializer(serializers.ModelSerializer):
    project = UltraLeanProjectSerializer(read_only=True)
    title = serializers.CharField(source='text_title')
    empty_positions = serializers.IntegerField(source='get_empty_positions')
    location = serializers.StringRelatedField()
    role = RoleSerializer()

    class Meta:
        model = StaffingRequest
        fields = ('id', 'title', 'project', 'empty_positions', 'role', 'location')


class RequestVendorSerializer(serializers.ModelSerializer):
    vendor = serializers.StringRelatedField()
    answer_display = serializers.StringRelatedField(source='get_answer_display')

    class Meta:
        model = RequestVendorRelationship
        fields = ('id', 'vendor', 'answer', 'answer_display', 'answered_at')


class RequestSerializer(serializers.ModelSerializer):
    vendors = serializers.SerializerMethodField()
    title = serializers.CharField(source='text_title')

    class Meta:
        model = StaffingRequest
        fields = ('id', 'title', 'vendors')

    def get_vendors(self, obj):
        vendors = obj.request_vendors.all()
        return RequestVendorSerializer(vendors, many=True).data
