"""
Shamelessly copied from rest_framework.settings

Settings for this library are all namespaced in the DRF_SNAP_TESTING setting.
For example your project's `settings.py` file might look like this:

DRF_SNAP_TESTING = {
    "DEFAULT_SNAP_CLASS": "drf_snap_testing.snap.Snap",
    "DEFAULT_BITS": [
        "drf_snap_testing.bits.Test",
        "drf_snap_testing.bits.Response",
        "drf_snap_testing.bits.Queries",
        "drf_snap_testing.bits.DatabaseDiff",
        "drf_snap_testing.bits.Mailbox",
    ],
}

This module provides the `snap_settings` object, that is used to access
this library settings, checking for user settings first, then falling
back to the defaults.
"""
from typing import Any, TypedDict, cast

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# Import from `django.core.signals` instead of the official location
# `django.test.signals` to avoid importing the test module unnecessarily.
from django.core.signals import setting_changed
from django.utils.module_loading import import_string


class Settings(TypedDict, total=False):
    DEFAULT_SNAP_CLASS: str
    DEFAULT_BITS: list[str]
    DEFAULT_GET_SNAP_PATH: str


DEFAULTS: Settings = {
    "DEFAULT_SNAP_CLASS": "drf_snap_testing.snap.Snap",
    "DEFAULT_BITS": [
        "drf_snap_testing.bits.FreezeGun",
        "drf_snap_testing.bits.TestInfo",
        # "drf_snap_testing.bits.DatabaseDiff",
        "drf_snap_testing.bits.Queries",
        # "drf_snap_testing.bits.Mailbox",
        "drf_snap_testing.bits.Response",
    ],
    "DEFAULT_GET_SNAP_PATH": "drf_snap_testing.bit.dynamic_path",
}


# List of settings that may be in string import notation.
IMPORT_STRINGS = [
    "DEFAULT_SNAP_CLASS",
    "DEFAULT_BITS",
    "DEFAULT_GET_SNAP_PATH",
]

# List of settings that may require an instanciate call
CREATE_INSTANCES = [
    "DEFAULT_BITS",
]


def perform_import(val: Any, setting_name: str) -> Any:
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None:
        return None
    if isinstance(val, str):
        return import_from_string(val, setting_name)
    if isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val: str, setting_name: str) -> Any:
    """
    Attempt to import a class from a string representation.
    """
    try:
        return import_string(val)
    except ImportError as err:
        msg = (
            f"Could not import '{val}' for API setting '{setting_name}'. "
            f"{err.__class__.__name__}: {err}."
        )
        raise ImportError(msg) from err


class SnapSettings:
    """
    A settings object that allows REST Framework settings to be accessed as
    properties. For example:

        from rest_framework.settings import api_settings
        print(api_settings.DEFAULT_RENDERER_CLASSES)

    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.

    Note:
    This is an internal class that is only compatible with settings namespaced
    under the DRF_SNAP_TESTING name. It is not intended to be used by 3rd-party
    apps, and test helpers like `override_settings` may not work as expected.
    """

    def __init__(
        self,
        user_settings: Settings | None = None,
        defaults: Settings | None = None,
        import_strings: list[str] | None = None,
        create_instances: list[str] | None = None,
    ):
        if user_settings:
            self._user_settings = user_settings
        self.defaults = defaults or DEFAULTS
        self.import_strings = import_strings or IMPORT_STRINGS
        self.create_instances = create_instances or CREATE_INSTANCES
        self._cached_attrs: set[str] = set()

    @property
    def user_settings(self) -> Settings:
        if not hasattr(self, "_user_settings"):
            user_settings = getattr(settings, "DRF_SNAP_TESTING", {})
            if not isinstance(user_settings, dict):
                raise ImproperlyConfigured(
                    "The DRF_SNAP_TESTING setting must be a dictionary"
                )
            self._user_settings = cast(Settings, user_settings)
        return self._user_settings

    def __getattr__(self, attr: str) -> Any:
        if attr not in self.defaults:
            raise AttributeError(f"Invalid API setting: {attr}")

        try:
            # Check if present in user settings
            val = self.user_settings[attr]  # type: ignore
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]  # type: ignore

        # Coerce import strings into classes
        if attr in self.import_strings:
            val = perform_import(val, attr)

        # Instantiate classes if needed
        if attr in self.create_instances and isinstance(val, type):
            val = val()

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self) -> None:
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")


snap_settings = SnapSettings(None, DEFAULTS, IMPORT_STRINGS)


def reload_api_settings(*_args: Any, **kwargs: Any) -> None:
    setting = kwargs["setting"]
    if setting == "DRF_SNAP_TESTING":
        snap_settings.reload()


setting_changed.connect(reload_api_settings)
