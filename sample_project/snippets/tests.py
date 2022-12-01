from django.test import TestCase


class SanityTest(TestCase):
    def test_is_sane(self) -> None:
        self.assertEqual(1, 1)
