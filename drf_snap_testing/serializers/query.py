from typing import Any

from rest_framework import serializers

from .base import ReadOnlySerializer
from .fields import SQLField


class QuerySerializer(ReadOnlySerializer[list[dict[str, Any]]]):
    """A serializer for django.db.connection.queries."""

    sql = SQLField()
    time = serializers.FloatField()
