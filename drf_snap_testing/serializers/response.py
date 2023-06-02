import json

from django.core.handlers.wsgi import WSGIRequest
from drf_yaml.styles import LiteralStr
from rest_framework import serializers
from rest_framework.response import Response

from .base import ReadOnlySerializer


class RequestSerializer(ReadOnlySerializer[WSGIRequest]):
    """A serializer for django.core.handlers.wsgi.WSGIRequest."""

    user = serializers.CharField()
    method = serializers.CharField()
    path = serializers.CharField()
    query_params = serializers.SerializerMethodField()
    headers = serializers.DictField()
    body = serializers.SerializerMethodField(required=False)

    def get_query_params(self, obj: WSGIRequest) -> str | None:
        """Return the query params as a string."""
        return obj.META.get("QUERY_STRING")

    def get_body(self, obj: WSGIRequest) -> LiteralStr | None:
        """Return the body as a YAML literal str."""
        body = obj.POST
        if not body:
            return None

        return LiteralStr(json.dumps(body, indent=2))


class ResponseSerializer(ReadOnlySerializer[Response]):
    """A serializer for rest_framework.response.Response."""

    status_code = serializers.IntegerField()
    headers = serializers.DictField()
    body = serializers.SerializerMethodField(required=False)

    def get_body(self, obj: Response) -> LiteralStr:
        """Return the body as a YAML literal str."""
        return LiteralStr(json.dumps(obj.data, indent=2))


class RequestResponseSerializer(ReadOnlySerializer[Response]):
    """
    A serializer for a request and its accompanying response.

    More accurately, this is a serializer for a rest_framework.response.Response
    and its accompanying django.core.handlers.wsgi.WSGIRequest.
    """

    request = RequestSerializer(source="wsgi_request")
    response = ResponseSerializer(source="*")
