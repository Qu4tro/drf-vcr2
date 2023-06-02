# ruff: noqa: D100,D101
from django.apps import AppConfig


class SampleAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "snippets"

    # pylint: disable=import-outside-toplevel
    def ready(self) -> None:
        """Import the monkeypatching code when the app is ready."""
        import django_stubs_ext
        from rest_framework import serializers, viewsets

        django_stubs_ext.monkeypatch(
            extra_classes=(
                viewsets.ReadOnlyModelViewSet,
                viewsets.ModelViewSet,
                serializers.HyperlinkedRelatedField,
            ),
        )
