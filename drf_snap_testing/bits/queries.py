from typing import Any, Literal, cast

from django.conf import settings
from django.db import connections, reset_queries

from ..bit import Bit
from ..serializers import QuerySerializer


class Queries(Bit):
    """
    A bit for the queries made during the request.

    Takes a dict of db alias to queries as the value.

    This is useful as it provides the queries made during the request.

    Example:
    -------
        >>> from django.db import connection
        >>> from drf_snap_testing.snap import Snap
        >>> from drf_snap_testing.bits import Queries
        >>> snap = Snap(bits=[Queries])
        >>> response = self.client.get("/foo/")
        >>> snap.add(queries={"default": connection.queries})

    """

    serializer_class = QuerySerializer
    ignore_list = [rb"^\s*-?\stime: \d+\.\d+$"]
    ignore_params = ["time"]

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the queries bit."""
        ignore_params = kwargs.pop("ignore_params", None)

        super().__init__(*args, **kwargs)
        self._ignore_params = ignore_params or getattr(self, "ignore_params", [])

    @property
    def data(self) -> dict[str, Any]:
        """Return the queries made during the request grouped by database."""
        queries_per_db = cast(dict[str, list[dict[str, Any]]], self.value)
        return {
            db_alias: self.serializer_class(
                instance=queries,
                many=True,
            ).data
            for db_alias, queries in queries_per_db.items()
        }

    def __enter__(self) -> None:
        """Start the data collection."""
        reset_queries()

    def __exit__(self, *args: Any) -> Literal[False]:
        """Stop the data collection."""
        self.value = {
            db_alias: connections[db_alias].queries for db_alias in settings.DATABASES
        }
        return False
