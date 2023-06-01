from typing import Any

from ..bit import Bit
from ..serializers import DictSerializer


class Starter(Bit):
    """
    This is a starter bit.

    This is meant to be used as a template for creating new bits.
    """

    serializer_class = DictSerializer

    @property
    def data(self) -> Any:
        """
        This is the property that returns the value of the bit
        and therefore the data that is serialized to disk.
        """
        return self.value
