from typing import Any

from ..bit import Bit
from ..serializers import DictSerializer


class Starter(Bit):
    """
    Starter bit.

    This is meant to be used as a template for creating new bits.
    """

    serializer_class = DictSerializer

    @property
    def data(self) -> Any:
        """
        Overridden property.

        This is the data that is passed to the serializer and
        eventually ends up rendered in the snapshot file.
        """
        return self.value
