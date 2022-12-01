from typing import Any

from django.test import TestCase
from drf_vcr.declarative import DeclarativeAPITestCase


class SanityTest(TestCase):
    def test_is_sane(self) -> None:
        self.assertEqual(1, 1)


class ContractualAPICommon(DeclarativeAPITestCase):
    url_pattern_name = "Contractual-list"
    method = "GET"
    user: dict[str, Any] = {}

    def setUp(self) -> None:
        ...

    class Contractual2022APITestCases:
        query_parameters = {"year": 2022}

        class SomethingElse:
            method = "POST"

        class SomethingElse2:
            user = None

    class Contractual2023APITestCases:
        query_parameters = {"year": 2023}
