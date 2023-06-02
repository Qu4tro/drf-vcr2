import functools
import re
import sys
from pathlib import Path
from typing import Any, Callable, TypedDict, cast

from drf_yaml.renderers import YAMLRenderer
from rest_framework import renderers, serializers


class SerializerParams(TypedDict):
    """The parameters passed to the serializer."""

    instance: Any
    many: bool
    context: dict[str, Any]


def dynamic_path(
    test: Callable[[Any], None],
    *_args: Any,
    **_kwargs: Any,
) -> Path:
    """Resolve the directory to save the file in."""
    # pylint: disable=protected-access
    # ruff: noqa: SLF001

    test_parent_class_name = test.__class__.__name__
    test_name = str(
        test._testMethodName,  # type: ignore [attr-defined]
    )
    if test_filepath := sys.modules[test.__class__.__module__].__file__:
        test_path = Path(test_filepath).resolve()
    else:
        msg = "Unable to find test file path. Please raise an issue."
        raise AssertionError(msg)

    return test_path.with_suffix("") / test_parent_class_name / test_name


class Bit:
    # ruff: noqa: PLR0913
    def __init__(  # pylint: disable=too-many-arguments
        self,
        key: str | None = None,
        renderer: renderers.BaseRenderer | None = None,
        serializer_class: type[serializers.Serializer[Any]] | None = None,
        many: bool | None = None,
        ignore_list: list[str] | None = None,
        filename: str | None = None,
    ) -> None:
        """
        Initialize the Bit.

        Args:
        ----
        serializer_class: The serializer class to use to serialize the data
        renderer: The renderer to use to serialize the data (default: YAMLRenderer)
        many: Whether or not the serializer is a many serializer (default: False)
        ignore_list: A list of keys to ignore when comparing the data (default: [])
        key: The key to use in the snapshot file (default: the class name)
        filename: The filename to save the snapshot to (default: the key + ".yaml").

        Each of these arguments can be set as a class attribute instead.
        """
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
        self.filename: str | None = cast(
            str | None,
            filename or getattr(self, "filename", f"{self.key}.yaml"),
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
        self.serializer_class: type[serializers.Serializer[Any]] = cast(
            type[serializers.Serializer[Any]],
            serializer_class or getattr(self, "serializer_class", None),
        )
        if self.serializer_class is None:
            msg = "serializer_class must be passed in or set on the class"
            raise AssertionError(msg)

        # Get the many by the following priority:
        # 1. The many passed in
        # 2. The many attribute on the class
        self.many = many if many is not None else getattr(self, "many", False)

        # The value and directory will be set after instantiation on the testcase itself
        self.value: Any | None = None
        self.directory: Path | None = None

    def filter_render(self, content: bytes) -> bytes:
        """Filter out lines that should not be compared."""
        lines = content.split(b"\n")

        for ignore in self.ignore_list:
            regex = re.compile(ignore)
            lines = [line for line in lines if not regex.match(line)]

        return b"\n".join(lines)

    @functools.cached_property
    def render(self) -> bytes:
        """Render the file."""
        return self.filter_render(self.unfiltered_render)

    @functools.cached_property
    def unfiltered_render(self) -> bytes:
        """Render the file."""
        if self.data is None:
            return b""

        return cast(bytes, self.renderer.render(self.data))

    @property
    def data(self) -> Any:
        """The data to render."""
        serializer_args: SerializerParams = {
            "instance": self.value,
            "many": self.many,
            "context": {},
        }
        return self.serializer_class(**serializer_args).data

    @property
    def path(self) -> Path:
        """The file path to save the file in."""
        if self.directory is None:
            msg = "directory must be set"
            raise AssertionError(msg)
        if self.filename is None:
            msg = "filename must be set"
            raise AssertionError(msg)

        return self.directory / self.filename

    @property
    def previous_render(self) -> bytes:
        """Read the current file."""
        try:
            return self.filter_render(self.path.read_bytes())
        except FileNotFoundError:
            return b""

    def write(self) -> None:
        """Save the file."""
        render = self.unfiltered_render
        if render:
            self.path.write_bytes(render)
