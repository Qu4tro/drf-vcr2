import sqlparse
from drf_yaml.styles import LiteralStr
from rest_framework import serializers


class SQLField(serializers.Field):  # type: ignore [type-arg]
    """A field that represents a SQL statement."""

    def to_representation(self, value: str) -> LiteralStr:
        """Format the SQL statement and represent it as a YAML literal str."""
        formatted = sqlparse.format(value, reindent=True, keyword_case="upper")
        if not isinstance(formatted, str):
            msg = "Expected a string."
            raise TypeError(msg)
        return LiteralStr(formatted)

    def to_internal_value(self, _data: LiteralStr) -> str:
        """Not implemented. Read-only field."""
        msg = "Not implemented yet."
        raise NotImplementedError(msg)
