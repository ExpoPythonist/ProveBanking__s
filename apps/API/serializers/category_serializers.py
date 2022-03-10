from rest_framework import serializers

from categories.models import Category


class CategorySerializer(serializers.ModelSerializer):
    label = serializers.CharField(source='name')
    value = serializers.CharField(source='id')

    class Meta:
        model = Category
        fields = ('id', 'name', 'kind', 'label', 'value')
