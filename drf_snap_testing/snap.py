from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from .bit import Bit
from .settings import snap_settings


@dataclass
class Snap:
    """
    A way to collect data from a single test, across several bits and write them to disk

    :param directory: The directory to write the snaps to
    :param bits: The bits to collect

    :raises AssertionError: If the bits do not have unique keys

    :Example:

    >>> from pathlib import Path
    >>> with Snap(directory=Path("snaps")) as snap:
    ...     response = self.client.get("/api/v1/users/")
    ...     snap.add(response=response)
    ...     snap.add(queries=connection.queries)
    >>> self.assertSnapEqual(snap)

    """

    directory: Path
    bits: list[Bit] = field(
        default_factory=lambda: [
            klass() if callable(klass) else klass
            for klass in snap_settings.DEFAULT_BITS
        ]
    )
    bits_by_keys: dict[str, Bit] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        """Ensure that the bits have unique keys"""
        self._populate_bits_by_keys()
        self._ensure_unique_bits()

    def __enter__(self) -> "Snap":
        """Start the data collection"""
        for bit in self.bits:
            if hasattr(bit, "__enter__"):
                bit.__enter__()

        return self

    def __exit__(self, *args: Any) -> Literal[False]:
        """Stop the data collection"""
        for bit in self.bits:
            if hasattr(bit, "__exit__"):
                bit.__exit__(*args)

        return False

    def add_bit(self, **kwargs: dict[str, Any]) -> None:
        """Add a bit info to snap"""
        for key, value in kwargs.items():
            try:
                bit = self.bits_by_keys[key]
            except KeyError as err:
                raise AssertionError(f"Unknown key {key}") from err

            bit.value = value

    def _ensure_unique_bits(self) -> None:
        """Ensure that the bits have unique keys"""
        if len(self.bits) != len(self.bits_by_keys):
            raise AssertionError("bits must have unique keys")

    def _populate_bits_by_keys(self) -> None:
        """Set the directory for each bit and populate the bits_by_keys dictionary"""
        for bit in self.bits:
            bit.directory = self.directory
            self.bits_by_keys[bit.key] = bit
