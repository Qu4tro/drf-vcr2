# ruff: noqa: D100,D101,D106

from drf_snap_testing import bits
from drf_snap_testing.testcase import SnapAPITestCase
from snippets.models import Snippet


class UserList(SnapAPITestCase):
    """somethingelse."""

    url_pattern_name = "user-list"

    class UserListAnon:
        """something."""

        user = None

    class UserListAnon2:
        """something1."""

        user = {"id": 1}


class SnippetTest(SnapAPITestCase):
    url_pattern_name = "snippet-list"
    method = "POST"
    data = {
        "title": "string",
        "code": "string",
        "linenos": True,
        "language": "abap",
        "style": "abap",
    }
    user = {"id": 1}

    class SnippetPostAuthed:
        ...

    class SnippetPostAuthedDbDiff:
        bits = [bits.DatabaseDiff(models=[Snippet])]


class SnippetDelete(SnapAPITestCase):
    bits = [
        bits.Queries(),
        bits.TestInfo(),
        bits.Response(),
        bits.DatabaseDiff(models=[Snippet]),
        bits.FreezeGun(),
        bits.Mailbox(),
        bits.VCR(),
    ]
    url_pattern_name = "snippet-detail"
    url_kwargs = {"pk": 1}
    method = "DELETE"
    user = {"id": 1}
