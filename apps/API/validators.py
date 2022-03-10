from rest_framework import serializers


def choice_validator(value):
    options = value.get('options')
    if not options:
        raise serializers.ValidationError('Options for choice field are required.')
    if not isinstance(options, list):
        raise serializers.ValidationError('Options must be a list of strings')
