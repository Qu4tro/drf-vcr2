import sqlparse
from drf_yaml.styles import literal_str
from rest_framework import serializers


class SQLField(serializers.Field):  # type: ignore
    """
    A field that represents a SQL statement.
    """

    def to_representation(self, value: str) -> literal_str:
        formatted = sqlparse.format(value, reindent=True, keyword_case="upper")
        if not isinstance(formatted, str):
            raise TypeError("Expected a string.")
        return literal_str(formatted)

    def to_internal_value(self, data: literal_str) -> str:
        raise NotImplementedError("Not implemented yet.")
