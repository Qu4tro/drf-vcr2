from rest_framework import serializers

from .base import ReadOnlySerializer


class DatabaseDiffSerializer(ReadOnlySerializer):
    diff = serializers.DictField(source="*")
