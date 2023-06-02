import json

from django.core.handlers.wsgi import WSGIRequest
from drf_yaml.styles import LiteralStr
from rest_framework import serializers
from rest_framework.response import Response

from .base import ReadOnlySerializer


class RequestSerializer(ReadOnlySerializer):
    user = serializers.CharField()
    method = serializers.CharField()
    path = serializers.CharField()
    query_params = serializers.SerializerMethodField()
    headers = serializers.DictField()
    body = serializers.SerializerMethodField(required=False)

    def get_query_params(self, obj: WSGIRequest) -> str | None:
        return obj.META.get("QUERY_STRING")

    def get_body(self, obj: WSGIRequest) -> LiteralStr | None:
        body = obj.POST
        if not body:
            return None

        return LiteralStr(json.dumps(body, indent=2))


class ResponseSerializer(ReadOnlySerializer):
    status_code = serializers.IntegerField()
    headers = serializers.DictField()
    body = serializers.SerializerMethodField(required=False)

    def get_body(self, obj: Response) -> LiteralStr:
        return LiteralStr(json.dumps(obj.data, indent=2))


class RequestResponseSerializer(ReadOnlySerializer):
    request = RequestSerializer(source="wsgi_request")
    response = ResponseSerializer(source="*")
