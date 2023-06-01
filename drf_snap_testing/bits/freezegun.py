from typing import Any, Literal

from freezegun import freeze_time

from ..bit import Bit


class FreezeGun(Bit):
    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        datetime = kwargs.pop("datetime", None)
        kwargs["serializer_class"] = kwargs.get("serializer_class", lambda: None)

        super().__init__(*args, **kwargs)
        self.freeze_datetime = datetime or getattr(
            self, "datetime", "2020-03-01 01:02:03"
        )
        self.freezer = freeze_time(self.freeze_datetime)

    def __enter__(self) -> "FreezeGun":
        self.freezer.start()
        return self

    def __exit__(self, *args: Any) -> Literal[False]:
        self.freezer.stop()
        return False

    @property
    def render(self) -> bytes:
        return b""

    @property
    def complete_render(self) -> bytes:
        return b""

    @property
    def data(self) -> None:
        return None
