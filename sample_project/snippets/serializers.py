# ruff: noqa: D100,D102,D101,D106

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Snippet

User = get_user_model()


class SnippetSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    highlight = serializers.HyperlinkedIdentityField(
        view_name="snippet-highlight",
        format="html",
    )

    class Meta:
        model = Snippet
        fields = [
            "url",
            "id",
            "highlight",
            "owner",
            "title",
            "code",
            "linenos",
            "language",
            "style",
        ]


class UserSerializer(serializers.HyperlinkedModelSerializer):
    snippets: serializers.HyperlinkedRelatedField[
        Snippet
    ] = serializers.HyperlinkedRelatedField(
        many=True,
        view_name="snippet-detail",
        read_only=True,
    )

    class Meta:
        model = User
        fields = ["url", "id", "username", "snippets"]
