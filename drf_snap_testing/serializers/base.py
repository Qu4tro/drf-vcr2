from rest_framework import serializers


class ReadOnlySerializer(serializers.Serializer[None]):
    def create(self, _validated_data: None) -> None:
        """This serializer is read-only."""
        raise TypeError("This serializer is read-only")

    def update(self, _instance: None, _validated_data: None) -> None:
        """This serializer is read-only."""
        raise TypeError("This serializer is read-only")
