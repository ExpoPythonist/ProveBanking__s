from rest_framework import serializers


from roles.models import Role


__all__ = ('RoleSerializer',)


class RoleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Role
        fields = ('id', 'name', 'color',)
