from ..bit import Bit
from ..serializers import TestInfoSerializer


class TestInfo(Bit):
    """
    A bit for information of the currently running test. Takes its class as the value.

    This is useful as it provides the test metadata, such as the test name, etc.

    Example:

        >>> from drf_snap_testing.snap import Snap
        >>> from drf_snap_testing.bits import TestInfo
        >>> snap = Snap(bits=[TestInfo])
        >>> snap.add(testinfo=self)
    """

    serializer_class = TestInfoSerializer
