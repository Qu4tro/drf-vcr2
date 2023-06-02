from typing import Any, Callable, Literal, Mapping

import vcr

from ..bit import Bit
from ..serializers import DictSerializer


def partition(
    dictionary: Mapping[Any, Any],
    condition: Callable[[Any, Any], bool],
) -> tuple[dict[Any, Any], dict[Any, Any]]:
    """Split a dictionary into two for a given boolean condition."""
    return (
        {k: v for k, v in dictionary.items() if condition(k, v)},
        {k: v for k, v in dictionary.items() if not condition(k, v)},
    )


class VCR(Bit):
    """
    A Bit that uses VCR to record and replay HTTP requests.

    Example:
    -------
        >>> with VCR(filename="test.yaml", directory="tests/vcr"):
        ...     requests.get("https://example.com")
    """

    serializer_class = DictSerializer

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the VCR bit.

        Args:
        ----
        *args: Arguments to pass to the Bit superclass.
        **kwargs: Keyword arguments split into two groups:
            - vcr_kwargs: Keyword arguments to pass to VCR.
            - init_kwargs: Keyword arguments to pass to the Bit superclass.
            The partition is based on the arguments to VCR's __init__ method.
        """
        default_vcr_kwargs: dict[str, Any] = {}

        vcr_kwargs, init_kwargs = partition(
            kwargs,
            lambda parameter_name, _: parameter_name
            in vcr.VCR.__init__.__code__.co_varnames,
        )
        super().__init__(*args, **init_kwargs)
        self.vcr = vcr.VCR(**default_vcr_kwargs, **vcr_kwargs)
        self.cassette: vcr.cassette.Cassette | None = None
        self.cassette_ctx: vcr.cassette.CassetteContextDecorator | None = None

    def __enter__(self) -> "VCR":
        """Enter VCR's context manager."""
        if not self.filename:
            msg = "filename must be set"
            raise ValueError(msg)
        if not self.directory:
            msg = "directory must be set"
            raise ValueError(msg)

        self.cassette_ctx = self.vcr.use_cassette(self.directory / self.filename)
        self.cassette_ctx.__enter__()
        self.cassette = (
            self.cassette_ctx._CassetteContextDecorator__cassette  # ruff: noqa: SLF001
        )
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> Literal[False]:
        """Exit VCR's context manager."""
        if self.cassette_ctx is not None:
            self.cassette_ctx.__exit__(*args, **kwargs)
        else:
            msg = "How did you get here? Raise an issue on GitHub."
            raise ValueError(msg)
        return False

    @property
    def previous_render(self) -> bytes:
        """Don't render anything, so that it never fails."""
        return b""

    @property
    def render(self) -> bytes:
        """Don't render anything, so that it never fails."""
        return b""
