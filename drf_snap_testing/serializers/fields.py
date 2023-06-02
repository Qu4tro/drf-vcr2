import sqlparse
from drf_yaml.styles import LiteralStr
from rest_framework import serializers


class SQLField(serializers.Field):  # type: ignore
    """
    A field that represents a SQL statement.
    """

    def to_representation(self, value: str) -> LiteralStr:
        formatted = sqlparse.format(value, reindent=True, keyword_case="upper")
        if not isinstance(formatted, str):
            raise TypeError("Expected a string.")
        return LiteralStr(formatted)

    def to_internal_value(self, data: LiteralStr) -> str:
        raise NotImplementedError("Not implemented yet.")
