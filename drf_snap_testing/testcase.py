import inspect
import re
import unittest
from collections import OrderedDict
from contextlib import ExitStack, contextmanager
from functools import partial
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Type, TypeVar, cast

import django
import rest_framework.test
from django.contrib.auth import get_user_model
from django.core import mail
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.test import APIClient

from .bit import Bit
from .bits import Starter
from .settings import snap_settings


@contextmanager
def multi_context_manager(*cms: Any) -> Any:
    "I give up trying to add type hints to this"
    with ExitStack() as stack:
        yield [
            stack.enter_context(cls)
            for cls in cms
            if hasattr(cls, "__enter__") and hasattr(cls, "__exit__")
        ]


SNAKE_CASE = re.compile("((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))")

TEST_KEYS = (
    "method",
    "data",
    "url_pattern_name",
    "url_kwargs",
    "user",
    "bits",
    "snap_class",
    "format",
    "content_type",
    "wsgi_request_extra",
)

_ATC_co = TypeVar("_ATC_co", bound="SnapAPITestCase", covariant=True)


class SnapTestCaseMetaclass(type):
    """
    Metaclass for SnapTestCase

    This metaclass is responsible for:
    - Ensuring each test class has the accumulated test attributes from its parents
    - Creating a new test method for each dangling test class.
    - Ensuring that each test method has the correct name, docstring and test attributes
    """

    def __new__(
        mcs: Type["SnapTestCaseMetaclass"],
        clsname: str,
        bases: tuple[Type[type]],
        attrs: dict[str, Any],
    ) -> "SnapTestCaseMetaclass":
        """
        TODO
        """
        # Only apply to subclasses of SnapTestCase
        if clsname.startswith("Snap") and clsname.endswith("TestCase"):
            return super().__new__(mcs, clsname, bases, attrs)

        # Build the test attributes mapping
        attrs["test_attributes_mapping"] = {}

        # Iterate through the test attributes
        for test_name, test_docstring, test_attrs in mcs.resolve_test_attrs(attrs):
            # Can't have repeated test names
            if test_name in attrs:
                raise AssertionError

            # Make a brand new test method with the test attributes information
            test_function = mcs.generic_wrapper(test_name=test_name)
            test_function.__name__ = test_name
            test_function.__doc__ = test_docstring
            test_function.__qualname__ = f"{clsname}.{test_name}"

            # Add the test method to the soon-to-be-created class
            attrs[test_name] = test_function
            # Add the test attributes to the soon-to-be-created class
            attrs["test_attributes_mapping"][test_name] = test_attrs

        # Create the class
        return super().__new__(mcs, clsname, bases, attrs)

    @classmethod
    def resolve_test_attrs(
        mcs: Type["SnapTestCaseMetaclass"],
        attrs: dict[str, Any],
        parent_test_attrs: dict[str, Any] | None = None,
    ) -> Iterator[tuple[str, str, dict[str, Any]]]:
        """
        Given a SnapTestCase attributes, it will convert them into a mapping
            of test name and test parameters.
        The SnapTestCase may have multiple levels of nested test classes.

        For example:
        >>> class RandomTestCase(SnapAPITestCase):
        ...     url_pattern_name = "Random-list"
        ...     method = "GET"
        ...     user: dict[str, Any] = {}

        ...     class TestCaseFor2022:
        ...         data = {"year": 2022}
        ...
        ...         class SomethingElse:
        ...             method = "POST"
        ...
        ...         class SomethingNew:
        ...             user = None
        ...
        ...     class TestCaseFor2023:
        ...         data = {"year": 2023}
        {
            "test_case_for_2023": {
                "url_pattern_name": "Random-list",
                "method": "GET",
                "user": {},
                "data": {"year": 2023},
            },
            "test_something_else": {
                "url_pattern_name": "Random-list",
                "method": "POST",
                "user": {},
                "data": {"year": 2022},
            },
            "test_something_new": {
                "url_pattern_name": "Random-list",
                "method": "GET",
                "user": None,
                "data": {"year": 2022},
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
            test_name = mcs.resolve_test_name(attrs)
            test_docstring = attrs.get("__doc__", None)
            yield test_name, test_docstring, new_test_attrs

        # If there are, figure out its attributes, recurse and yield from them
        for klass in test_classes:
            class_attrs = {
                **klass.__dict__,
                "__name__": klass.__name__,
                "__doc__": klass.__doc__,
            }
            yield from mcs.resolve_test_attrs(class_attrs, new_test_attrs)

    @staticmethod
    def resolve_test_name(attrs: dict[str, Any]) -> str:
        "Determine the test name given the attributes of a class"

        # If the class has a test_name attribute, use it
        test_name = attrs.get("test_name")
        if test_name is None:
            try:
                # If it doesn't, use the class name
                class_name = attrs["__name__"]
            except KeyError:
                # If it doesn't have a name, use the qualname
                class_name = attrs["__qualname__"].rsplit(".", maxsplit=1)[-1]

            # Convert the class name to snake case
            test_name = SNAKE_CASE.sub(r"_\1", class_name).lower()

        # If the test name doesn't start with "test_", add it
        if test_name.startswith("test_"):
            return test_name
        return f"test_{test_name}"

    @staticmethod
    def generic_wrapper(test_name: str) -> Callable[[_ATC_co], None]:
        """
        Wrapper used to create a closure out of the generic test, so that
        variables can be included in it at "build time"
        """

        @override_settings(DEBUG=True)
        def generic(self: "SnapAPITestCase") -> None:
            """
            Source generic test method for the test methods of the SnapTestCase classes

            It takes its test attributes from test_attributes_mapping class attribute.

            Under Snap's context manager, it will perform a request to the API
            using that data, while retrieving / executing all the specified bits.

            It will then assert that the collected data matches the recorded data.
            """
            # Get the test attributes
            tam = self.test_attributes_mapping[test_name]

            # Authenticate and build the request
            SnapGenericHelper.authenticate(self.client, tam)
            request = SnapGenericHelper.build_request(self.client, tam)
            bits = SnapGenericHelper.get_bit_instances(tam)

            # Get the test directory and set it for each bit
            test_directory = SnapGenericHelper.get_test_directory(self, tam)
            test_directory.mkdir(parents=True, exist_ok=True)
            for _, bit in bits.items():
                bit.directory = test_directory

            # It's important to retrieve the bits inside snap's context manager
            # as some bits have __enter__ and __exit__ methods that need to be
            # called.
            with multi_context_manager(*bits.values()):
                # Execute the request
                response = request()
                # Set the value of each bit
                bits.get("response", Starter()).value = response
                bits.get("testinfo", Starter()).value = self
                bits.get("mailbox", Starter()).value = mail.outbox

            # It's important to do this outside of the context manager
            # as the context manager closing may change the state of the
            # objects being snapshotted.
            self.assertSnapEquals(bits.values())

        return generic


class SnapGenericHelper:
    @staticmethod
    def authenticate(client: APIClient, tam: Mapping[str, Any]) -> None:
        """
        Authenticate the client using the user specified in the test attributes

        If the user test attribute is None, don't authenticate
        If the user test attribute is a dict:
            - Interpret it as a filter
            - Get the user from the database
            - Authenticate the client using the user
        """
        request_user_filters = tam.get("user")
        if request_user_filters is not None:
            user = get_user_model().objects.get(**request_user_filters)
            client.force_authenticate(user)

    @staticmethod
    def build_request(
        client: APIClient, tam: Mapping[str, Any]
    ) -> Callable[[], Response]:
        """
        Make a request to the API using:
            - method (default: GET)
            - url_pattern_name
            - data (optional)
            - format (optional)
            - content_type (optional)
            - wsgi_request_extra (optional)
        """
        # Get the HTTP method to be used in the request
        method = tam.get("method", "GET").lower()

        # Get the HTTP method from the client
        try:
            http_call = getattr(client, method)
        except AttributeError as err:
            raise NotImplementedError(
                f"APIClient doesn't implement the {method} method"
            ) from err

        # Get the URL path to be used in the request
        url_kwargs = tam.get("url_kwargs", {})
        url = reverse(tam["url_pattern_name"], kwargs=url_kwargs)

        # If the method is not GET, the user may want to specify the
        #  format and content_type of the request
        http_kwargs: dict[str, str | None] = {}
        if method != "get":
            http_kwargs = {
                "drf_format": tam.get("format"),
                "content_type": tam.get("content_type"),
            }

        # WSGIRequest extra kwargs
        extra = tam.get("wsgi_request_extra", {})

        # Make the request
        return partial(http_call, url, data=tam.get("data"), **http_kwargs, **extra)

    @staticmethod
    def get_test_directory(test: Any, tam: Mapping[str, Any]) -> Path:
        """
        Build the get_test_directory partial function to be used by the bits
        """
        get_test_directory_func = tam.get(
            "get_test_directory",
            snap_settings.DEFAULT_GET_SNAP_PATH,
        )
        return cast(Path, get_test_directory_func(test=test, test_attributes=tam))

    @staticmethod
    def get_bit_instances(tam: Mapping[str, Any]) -> OrderedDict[str, Bit]:
        bits: OrderedDict[str, Bit] = OrderedDict()
        # For each bit,
        # If it's a class instantiate it and add it to the list
        # If it's an instance, add it to the list
        for bit in cast(
            Iterable[Bit | Type[Bit]],
            tam.get("bits", snap_settings.DEFAULT_BITS),
        ):
            if isinstance(bit, type):
                bit = bit()

            bits[bit.key] = bit

        return bits


class SnapTestCase(unittest.TestCase, metaclass=SnapTestCaseMetaclass):
    """
    TestCase subclass that adds the ability to take snapshots of the test

    It's recommended to use SnapDjangoTestCase or SnapAPITestCase instead of this class
    """

    test_attributes_mapping: dict[str, Any]

    # pylint: disable=invalid-name
    def assertSnapEquals(self, bits: Iterable[Bit]) -> None:
        """
        Assert that the snapshots in the Snap are equal to the ones on file
        """
        last_err = None
        for bit in bits:
            try:
                self.assertEqual(bit.render, bit.previous_render)
            except AssertionError as err:
                last_err = err
                bit.write()

        if last_err is not None:
            raise last_err


class SnapDjangoTestCase(SnapTestCase, django.test.TestCase):
    """
    TestCase subclass that adds the SnapTestCase functionality to Django's TestCase

    It's recommended to use this class instead of SnapTestCase, as it provides
    some additional functionality.
    """


class SnapAPITestCase(SnapTestCase, rest_framework.test.APITestCase):
    """
    TestCase subclass that adds the SnapTestCase functionality to DRF's APITestCase

    It's recommended to use this class instead of SnapTestCase, as it provides
    some additional functionality.
    """
