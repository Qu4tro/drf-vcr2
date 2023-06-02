from typing import Any, TypeVar

from rest_framework import serializers

T = TypeVar("T")


class ReadOnlySerializer(serializers.Serializer[T]):
    """A serializer that is read-only."""

    def create(self, _validated_data: None) -> T:
        """Do nothing. Serializer is read-only."""
        msg = "This serializer is read-only"
        raise TypeError(msg)

    def update(self, _instance: T, _validated_data: None) -> T:
        """Do nothing. Serializer is read-only."""
        msg = "This serializer is read-only"
        raise TypeError(msg)


class DictSerializer(ReadOnlySerializer[dict[str, Any]]):
    obj = serializers.DictField(source="*")
