import inspect
import re
from typing import Any, Callable, Iterator, Type, TypeVar
from urllib.parse import urlencode

import rest_framework.test
from django.contrib.auth import get_user_model
from django.urls import reverse

SNAKE_CASE = re.compile("((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))")

TEST_KEYS = (
    "method",
    "query_parameters",
    "url_pattern_name",
    "user",
)

_ATC_co = TypeVar("_ATC_co", bound="DeclarativeAPITestCase", covariant=True)


class DeclarativeAPITestCaseMetaclass(type):
    def __new__(
        cls: Type["DeclarativeAPITestCaseMetaclass"],
        clsname: str,
        bases: tuple[Type[type]],
        attrs: dict[str, Any],
    ) -> "DeclarativeAPITestCaseMetaclass":
        """
        TODO

        """
        if clsname == "DeclarativeAPITestCase":
            return super().__new__(cls, clsname, bases, attrs)

        attrs["test_attributes_mapping"] = {}
        for test_name, test_attrs in cls.resolve_test_attrs(attrs):
            if test_name in attrs:
                raise AssertionError

            test_function = cls.generic_wrapper(test_name=test_name)
            test_function.__name__ = test_name
            test_function.__qualname__ = f"{clsname}.{test_name}"

            attrs[test_name] = test_function
            attrs["test_attributes_mapping"][test_name] = test_attrs

        return super().__new__(cls, clsname, bases, attrs)

    @classmethod
    def resolve_test_attrs(
        cls,
        attrs: dict[str, Any],
        parent_test_attrs: dict[str, Any] | None = None,
    ) -> Iterator[tuple[str, dict[str, Any]]]:
        """
        Given a DeclarativeAPITestCase attributes, it will convert them into a mapping
            of test name and test parameters.
        The DeclarativeAPITestCase may have multiple levels of nested test classes.

        For example:
        >>> class RandomTestCase(DeclarativeAPITestCase):
        ...     url_pattern_name = "Random-list"
        ...     method = "GET"
        ...     user: dict[str, Any] = {}

        ...     class TestCaseFor2022:
        ...         query_parameters = {"year": 2022}
        ...         class SomethingElse:
        ...             method = "POST"
        ...         class SomethingNew:
        ...             user = None
        ...     class TestCaseFor2023:
        ...         query_parameters = {"year": 2023}
        {
            "test_case_for_2023": {
                "url_pattern_name": "Random-list",
                "method": "GET",
                "user": {},
                "query_parameters": {"year": 2023},
            },
            "test_something_else": {
                "url_pattern_name": "Random-list",
                "method": "POST",
                "user": {},
                "query_parameters": {"year": 2022},
            },
            "test_something_new": {
                "url_pattern_name": "Random-list",
                "method": "GET",
                "user": None,
                "query_parameters": {"year": 2022},
            },
        }
        """
        # parent_test_attrs defaults to empty dict
        if parent_test_attrs is None:
            parent_test_attrs = {}

        # Get all attributes that match the expected test parameters
        test_attrs = {name: value for name, value in attrs.items() if name in TEST_KEYS}

        # Merge the obtained attributes with parent_test_attrs
        new_test_attrs = {**parent_test_attrs, **test_attrs}

        # Find any children the current resolving class may have
        test_classes = [klass for klass in attrs.values() if inspect.isclass(klass)]
        if not test_classes:
            # If there are none, get its name and yield the (name, attrs) pair
            test_name = cls.resolve_test_name(attrs)
            yield test_name, new_test_attrs

        # If there are, figure out its attributes, recurse and yield from them
        for klass in test_classes:
            class_attrs = {
                **klass.__dict__,
                "__name__": klass.__name__,
            }
            yield from cls.resolve_test_attrs(class_attrs, new_test_attrs)

    @staticmethod
    def resolve_test_name(attrs: dict[str, Any]) -> str:
        "Determine the test name given the attributes of a class"

        test_name = attrs.get("test_name")
        if test_name is None:
            try:
                class_name = attrs["__name__"]
            except KeyError:
                class_name = attrs["__qualname__"].rsplit(".", maxsplit=1)[-1]

            test_name = SNAKE_CASE.sub(r"_\1", class_name).lower()

        if test_name.startswith("test_"):
            return test_name

        return f"test_{test_name}"

    @staticmethod
    def generic_wrapper(test_name: str) -> Callable[[_ATC_co], None]:
        """
        Wrapper used to create a closure out of the generic test, so that
        variables can be included in it at "build time"
        """

        def generic(self: "DeclarativeAPITestCase") -> None:
            user_filters = self.test_attributes_mapping[test_name]["user"]
            if user_filters is not None:
                user = get_user_model().objects.get(**user_filters)
                self.client.force_authenticate(user)

            url = reverse(self.test_attributes_mapping[test_name]["url_pattern_name"])
            query_parameters = self.test_attributes_mapping[test_name][
                "query_parameters"
            ]
            if query_parameters:
                url += "?" + urlencode(query_parameters)

            response = self.client.get(url, format="json")

        return generic


class DeclarativeAPITestCase(
    rest_framework.test.APITestCase,
    metaclass=DeclarativeAPITestCaseMetaclass,
):
    test_attributes_mapping: dict[str, Any]
