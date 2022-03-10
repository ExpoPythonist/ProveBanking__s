from rest_framework import serializers

from watson.models import SearchEntry


__all__ = ('SearchSerializer',)


class SearchSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    value = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    order = serializers.SerializerMethodField()
    group = serializers.SerializerMethodField()


    ORDER = {
        'vendor': 1,
        'project': 2,
        'user': 3
    }

    CTYPE_LABELS = {
        'user': 'people',
        'vendor': 'suppliers'
    }

    class Meta:
        model = SearchEntry
        fields = ('label', 'value', 'title', 'url', 'order', 'group')

    def get_order(self, obj):
        return self.ORDER.get(obj.content_type.name, 90)

    def get_title(self, obj):
        if len(obj.title) > 30:
            return '{}...'.format(obj.title[:30])
        else:
            return obj.title

    def get_label(self, obj):
        return self.CTYPE_LABELS.get(obj.content_type.name) \
            or obj.content_type.name + 's'

    def get_value(self, obj):
        return '{}-{}'.format(obj.content_type.id, obj.object_id)

    def get_group(self, obj):
        return 'results'
