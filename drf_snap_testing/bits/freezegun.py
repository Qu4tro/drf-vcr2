from typing import Any, Literal

from freezegun import freeze_time

from ..bit import Bit


class FreezeGun(Bit):
    """
    A bit for freezing the datetime.

    Args:
    ----
    datetime (str, default="2020-03-01 01:02:03"): The datetime to freeze to.
    *args: The args to pass to the Bit class.
    **kwargs: The kwargs to pass to the Bit class.
    """

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the freeze gun.

        Args:
        ----
        datetime: The datetime to freeze to.
        *args: The args to pass to the Bit class.
        **kwargs: The kwargs to pass to the Bit class.
        """
        datetime = kwargs.pop("datetime", None)
        kwargs["serializer_class"] = kwargs.get("serializer_class", lambda: None)

        super().__init__(*args, **kwargs)
        self.freeze_datetime = datetime or getattr(
            self,
            "datetime",
            "2020-03-01 01:02:03",
        )
        self.freezer = freeze_time(self.freeze_datetime)

    def __enter__(self) -> "FreezeGun":
        """Start to mock the datetime."""
        self.freezer.start()
        return self

    def __exit__(self, *args: Any) -> Literal[False]:
        """Stop mocking the datetime."""
        self.freezer.stop()
        return False

    @property
    def render(self) -> bytes:
        """Don't render anything, so that it never fails."""
        return b""

    @property
    def complete_render(self) -> bytes:
        """Don't render anything, so that it never fails."""
        return b""

    @property
    def data(self) -> None:
        """Don't render anything, so that it never fails."""
        return
