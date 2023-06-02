import sys
from pathlib import Path
from typing import Any, Callable, cast

from rest_framework import serializers

from .base import ReadOnlySerializer


class TestInfoSerializer(ReadOnlySerializer[Callable[[Any], None]]):
    """
    Serializer for the test info.

    instance: The test instance
    """

    name = serializers.SerializerMethodField()
    parent_class_name = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()

    def get_name(self, obj: Any) -> str:
        """Name of the test."""
        # pylint: disable=protected-access
        return cast(str, obj._testMethodName)  # ruff: noqa: SLF001

    def get_parent_class_name(self, obj: Any) -> str:
        """Name of the parent class."""
        return cast(str, obj.__class__.__name__)

    def get_path(self, obj: Any) -> str:
        """Path to the test file."""
        if (filepath := sys.modules[obj.__class__.__module__].__file__) is None:
            msg = "Module has no __file__ attribute"
            raise ValueError(msg)

        return str(Path(filepath).resolve())
