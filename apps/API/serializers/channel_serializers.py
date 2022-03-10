from rest_framework import serializers

from channels.models import Channel, Message
from user_serializers import UserSerializer

__all__ = ('ChannelSerializer', 'MessageSerializer')


class MessageSerializer(serializers.ModelSerializer):
    mentions = serializers.SerializerMethodField()
    viewed = UserSerializer(many=True, read_only=True)
    posted_by = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'body', 'mentions', 'viewed', 'posted_by', 'created')

    def get_mentions(self, obj):
        users = obj.mentions.all()
        if users:
            return UserSerializer(users, many=True, read_only=True).data


class ChannelSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Channel
        fields = ('id', 'name', 'content_type', 'object_id', 'created', 'users', 'created_by', 'messages')

    def to_internal_value(self, data):
        collaborators = data.get('collaborators')
        data = super(ChannelSerializer, self).to_internal_value(data)
        if collaborators is not None:
            collaborators = get_user_model().objects.filter(id__in=collaborators)
            data['collaborators'] = collaborators
        return data
