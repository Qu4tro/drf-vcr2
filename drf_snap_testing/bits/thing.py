from typing import Any

from ..bit import Bit


class Thing(Bit):
    """
    A bit for anything. Takes any value as the value.

    This is useful for when you want to test a specific value, but don't want to
    write a custom serializer for it.

    This works as long as the value can be serialized by the yaml serializer.

    Example:
    -------
        >>> from drf_snap_testing.bits import Thing
        >>> thing = Thing()
        >>> thing.value = "test"
        >>> thing.write()
    """

    @property
    def data(self) -> Any:
        """Return the value it was set to."""
        return self.value
