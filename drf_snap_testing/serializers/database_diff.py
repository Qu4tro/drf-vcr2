from rest_framework import serializers

from .base import ReadOnlySerializer


# TODO: Change this to DictSerializer
class DatabaseDiffSerializer(ReadOnlySerializer[dict[str, str]]):
    diff = serializers.DictField(source="*")
