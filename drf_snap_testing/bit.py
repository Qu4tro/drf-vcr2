import re
from functools import cached_property
from pathlib import Path
from typing import Any, TypedDict, cast

from drf_yaml.renderers import YAMLRenderer
from rest_framework import renderers, serializers


class SerializerParams(TypedDict):
    instance: Any
    many: bool
    context: dict[str, Any]


class Bit:
    def __init__(  # pylint: disable=too-many-arguments
        self,
        key: str | None = None,
        renderer: renderers.BaseRenderer | None = None,
        serializer_class: type[serializers.Serializer[Any]] | None = None,
        many: bool = False,
        ignore_list: list[str] | None = None,
        filename: str | None = None,
    ) -> None:
        # Get the key by the following priority:
        # 1. The key passed in
        # 2. The key attribute on the class
        # 3. Default: The class name
        self.key: str = cast(
            str,
            key or getattr(self, "key", self.__class__.__name__.lower()),
        )
        # Get the filename by the following priority:
        # 1. The filename passed in
        # 2. The filename attribute on the class
        # 3. Default: The key + ".yaml"
        self.filename: str = cast(
            str,
            filename or getattr(self, "filename", self.key + ".yaml"),
        )
        # Get the renderer by the following priority:
        # 1. The renderer passed in
        # 2. The renderer attribute on the class
        # 3. Default: YAMLRenderer
        self.renderer: renderers.BaseRenderer = cast(
            renderers.BaseRenderer,
            renderer or getattr(self, "renderer", YAMLRenderer()),
        )
        # Get the ignore_list by the following priority:
        # 1. The ignore_list passed in
        # 2. The ignore_list attribute on the class
        # 3. Default: []
        self.ignore_list: list[bytes] = cast(
            list[bytes],
            ignore_list or getattr(self, "ignore_list", []),
        )

        # Get the serializer_class by the following priority:
        # 1. The serializer_class passed in
        # 2. The serializer_class attribute on the class
        self.serializer_class: type[serializers.Serializer[Any]] = (
            serializer_class or getattr(self, "serializer_class", None)
        )
        if self.serializer_class is None:
            raise AssertionError(
                "serializer_class must be passed in or set on the class"
            )

        # Get the many by the following priority:
        # 1. The many passed in
        # 2. The many attribute on the class
        self.many = many if many is not None else getattr(self, "many", False)

        # The directory and value will be set after instantiation on the
        # testcase itself.
        self.directory: Path | None = None
        self.value: Any | None = None

    @property
    def path(self) -> Path:
        """The path to read / write the file in"""
        if self.directory is None:
            raise AssertionError("directory must be set before path is accessed")
        return self.directory / self.filename

    def filter(self, content: bytes) -> bytes:
        """Filter out lines that should not be compared"""
        lines = content.split(b"\n")

        for ignore in self.ignore_list:
            regex = re.compile(ignore)
            lines = [line for line in lines if not regex.match(line)]

        return b"\n".join(lines)

    @cached_property
    def render(self) -> bytes:
        """Render the file"""
        return self.filter(self.complete_render)

    @cached_property
    def complete_render(self) -> bytes:
        """Render the file"""
        rendered = cast(bytes, self.renderer.render(self.data))
        return rendered

    @property
    def data(self) -> dict[str, Any]:
        """The data to render"""

        serializer_args: SerializerParams = {
            "instance": self.value,
            "many": self.many,
            "context": {},
        }
        return self.serializer_class(**serializer_args).data

    @property
    def current_render(self) -> bytes:
        """Read the current file"""
        try:
            return self.filter(self.path.read_bytes())
        except FileNotFoundError:
            return b""

    def write(self) -> None:
        """Save the file"""
        render = self.complete_render

        if render:
            self.path.write_bytes(self.complete_render)
