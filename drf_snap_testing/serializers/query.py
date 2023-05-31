from rest_framework import serializers

from .base import ReadOnlySerializer
from .fields import SQLField


class QuerySerializer(ReadOnlySerializer):
    sql = SQLField()
    time = serializers.FloatField()
