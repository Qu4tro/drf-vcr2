import sys
from pathlib import Path
from typing import Any

from rest_framework import serializers

from .base import ReadOnlySerializer


class TestInfoSerializer(ReadOnlySerializer):
    name = serializers.SerializerMethodField()
    parent_class_name = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()

    def get_name(self, obj: Any) -> str:
        # pylint: disable=protected-access
        return obj._testMethodName  # type: ignore

    def get_parent_class_name(self, obj: Any) -> str:
        """The name of the parent class"""
        return obj.__class__.__name__  # type: ignore

    def get_path(self, obj: Any) -> str:
        if (filepath := sys.modules[obj.__class__.__module__].__file__) is None:
            raise ValueError("Module has no __file__ attribute")

        return str(Path(filepath).resolve())
