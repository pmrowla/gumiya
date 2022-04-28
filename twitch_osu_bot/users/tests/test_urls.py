from django.urls import resolve, reverse
from test_plus.test import TestCase


class TestUserURLs(TestCase):
    """Test URL patterns for users app."""

    def setUp(self):
        self.user = self.make_user()

    def test_redirect_reverse(self):
        """users:redirect should reverse to /profile/~redirect/."""
        self.assertEqual(reverse("users:redirect"), "/profile/~redirect/")

    def test_redirect_resolve(self):
        """/profile/~redirect/ should resolve to users:redirect."""
        self.assertEqual(resolve("/profile/~redirect/").view_name, "users:redirect")

    def test_detail_reverse(self):
        """users:detail should reverse to /profile/."""
        self.assertEqual(reverse("users:detail"), "/profile/")

    def test_detail_resolve(self):
        """/profile/ should resolve to users:detail."""
        self.assertEqual(resolve("/profile/").view_name, "users:detail")

    def test_osu_reverse(self):
        """users:osu-account should reverse to /profile/~osu-account/."""
        self.assertEqual(reverse("users:osu-account"), "/profile/~osu-account/")

    def test_update_resolve(self):
        """/profile/~update/ should resolve to users:osu-account."""
        self.assertEqual(
            resolve("/profile/~osu-account/").view_name, "users:osu-account"
        )
