from drf_snap_testing.testcase import SnapAPITestCase


class UserList(SnapAPITestCase):
    "somethingelse"
    url_pattern_name = "user-list"

    class UserListAnon:
        "something"
        user = None

    class UserListAnon2:
        "something1"
        user = {"id": 1}


class SnippetTest(SnapAPITestCase):
    url_pattern_name = "snippet-list"

    class SnippetPostAuthed:
        method = "POST"
        data = {
            "title": "string",
            "code": "string",
            "linenos": True,
            "language": "abap",
            "style": "abap",
        }
        user = {"id": 1}
