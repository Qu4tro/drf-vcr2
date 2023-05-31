import inspect
import re
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, Type, TypeVar

import django
import rest_framework.test
from django.conf import settings
from django.contrib.auth import get_user_model

# from django.core import mail
from django.db import connections
from django.test.utils import override_settings
from django.urls import reverse

from .settings import snap_settings
from .snap import Snap


# TODO: It would be nice to have a way to override this
@dataclass
class TestInfo:
    func: Callable[..., None]

    @property
    def test_parent_class_name(self) -> str:
        """The name of the parent class"""
        return self.func.__class__.__name__

    @property
    def test_name(self) -> str:
        """The name of the test"""
        # pylint: disable=protected-access
        return self.func._testMethodName  # type: ignore

    @property
    def test_path(self) -> Path:
        """The path to the test file"""
        if (filepath := sys.modules[self.func.__class__.__module__].__file__) is None:
            raise ValueError("Module has no __file__ attribute")

        return Path(filepath).resolve()

    @property
    def directory(self) -> Path:
        """The directory to save the file in"""
        # TODO: It would be nice to have a way to configure 
        # whether the test_parent_class_name is present or not
        return (
            self.test_path.with_suffix("")
            / self.test_parent_class_name
            / self.test_name
        )


SNAKE_CASE = re.compile("((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))")

TEST_KEYS = (
    "method",
    "data",
    "url_pattern_name",
    "user",
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
            # Get the test attributes
            tam = self.test_attributes_mapping[test_name]

            # Get the user to be used in the request
            # If the user is None, don't authenticate
            # If the user is a dict, interpret it as a filter,
            #   get the user from the database and authenticate
            request_user_filters = tam.get("user")
            if request_user_filters is not None:
                user = get_user_model().objects.get(**request_user_filters)
                self.client.force_authenticate(user)

            # Get the snap collection class and snap classes from the test attributes
            snap_class = tam.get(
                "snap_class",
                snap_settings.DEFAULT_SNAP_CLASS,
            )
            bits = tam.get(
                "bits",
                [
                    klass() if callable(klass) else klass
                    for klass in snap_settings.DEFAULT_BITS
                ],
            )

            # Get the HTTP method to be used in the request
            method = tam.get("method", "GET").lower()

            # Get the HTTP method from the client
            try:
                http_call = getattr(self.client, method)
            except AttributeError as err:
                raise NotImplementedError(
                    f"APIClient doesn't implement the {method} method"
                ) from err

            # Get the URL path to be used in the request
            path = reverse(tam["url_pattern_name"])

            # If the method is not GET, the user may want to specify the
            #  format and content_type of the request
            http_kwargs: dict[str, str] = {}
            if method != "get":
                http_kwargs = {
                    "drf_format": tam.get("format"),
                    "content_type": tam.get("content_type"),
                }

            # WSGIRequest extra kwargs
            extra = tam.get("wsgi_request_extra", {})

            # Snap
            with snap_class(bits=bits, directory=TestInfo(self).directory) as snap:
                # Make the request
                response = http_call(path, data=tam.get("data"), **http_kwargs, **extra)

                # Collect the snapshots and add them to the Snap
                snap.add_bit(response=response)
                snap.add_bit(testinfo=self)
                snap.add_bit(
                    queries={
                        db_alias: connections[db_alias].queries
                        for db_alias in settings.DATABASES
                    }
                )
                # TODO: snap.add_bit(mailbox=mail.outbox)

                # Ensure the snapshots are equal to the ones on file
                self.assertSnapEquals(snap)

        return generic


class SnapTestCase(unittest.TestCase, metaclass=SnapTestCaseMetaclass):
    """
    TestCase subclass that adds the ability to take snapshots of the test

    It's recommended to use SnapDjangoTestCase or SnapAPITestCase instead of this class
    """

    test_attributes_mapping: dict[str, Any]

    # pylint: disable=invalid-name
    def assertSnapEquals(self, snap: Snap) -> None:
        """
        Assert that the snapshots in the Snap are equal to the ones on file
        """
        for bit in snap.bits:
            try:
                self.assertEqual(bit.render, bit.current_render)
            except AssertionError as err:
                if bit.directory is None:
                    raise AssertionError("Create an issue with this traceback") from err
                bit.directory.mkdir(parents=True, exist_ok=True)
                bit.write()
                # TODO: Raise only at the end
                raise err


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
