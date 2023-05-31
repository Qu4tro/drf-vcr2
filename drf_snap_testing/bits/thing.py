from typing import Any

from ..bit import Bit


class Thing(Bit):
    """
    A bit for anything. Takes any value as the value.

    This is useful for when you want to test a specific value, but don't want to
    write a custom serializer for it.

    This works as long as the value can be serialized by the yaml serializer.

    Example:

        >>> from drf_snap_testing.snap import Snap
        >>> from drf_snap_testing.bits import Thing
        >>> snap = Snap(bits=[Thing(key="foo")])
        >>> snap.add(foo="bar")
    """

    def data(self) -> Any:
        return self.value
