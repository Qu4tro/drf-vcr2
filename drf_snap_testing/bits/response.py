from ..bit import Bit
from ..serializers import RequestResponseSerializer


class Response(Bit):
    """
    A bit for the response of the request. Takes the response object as the value.

    This is useful as it provides the response and request data,
    such as the query params, status code, response body, etc.

    Example:

        >>> from drf_snap_testing.snap import Snap
        >>> from drf_snap_testing.bits import Response
        >>> snap = Snap(bits=[Response])
        >>> response = self.client.get("/foo/")
        >>> snap.add(response=response)
    """

    serializer_class = RequestResponseSerializer
