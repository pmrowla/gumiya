# -*- coding: utf-8 -*-
from datetime import timedelta
from unittest.mock import MagicMock, patch

from test_plus.test import TestCase

from ..models import OsuUsernameConfirmation
from .factories import OsuUsernameFactory, UserFactory


class TestUser(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test__str__(self):
        self.assertEqual(self.user.__str__(), self.user.username)


class TestOsuUsername(TestCase):
    def setUp(self):
        self.osu_user = OsuUsernameFactory()
        self.verified_user = OsuUsernameFactory(verified=True)

    def test__str__(self):
        self.assertEqual(
            self.osu_user.__str__(),
            "{} ({})".format(self.osu_user.username, self.osu_user.user),
        )

    @patch("twitch_osu_bot.users.models.OsuUsernameConfirmation.create")
    @patch("twitch_osu_bot.users.models.messages.info")
    def test_send_confirmation(self, mock_info, mock_create):
        confirmation = MagicMock()
        confirmation.key = "foo"
        request = MagicMock()
        mock_create.return_value = confirmation
        self.assertEqual(
            self.osu_user.send_confirmation(request=request, message=True), confirmation
        )
        mock_info.assert_called_once_with(
            request,
            "To verify your account, PM the following message in game to "
            " (verification key will expire in 15 minutes): !verify foo",
        )

    def test_change(self):
        request = MagicMock()
        self.assertTrue(self.verified_user.verified)
        self.verified_user.change(request, "foo")
        self.assertEqual(self.verified_user.username, "foo")
        self.assertFalse(self.verified_user.verified)


class TestOsuUsernameConfirmation(TestCase):
    def setUp(self):
        self.osu_user = OsuUsernameFactory()
        self.confirmation = OsuUsernameConfirmation.create(self.osu_user)

    def test_create(self):
        self.assertEqual(len(self.confirmation.key), 12)

    @patch("twitch_osu_bot.users.models.timezone.now")
    def test_key_expired(self, mock_now):
        mock_now.return_value = self.confirmation.created
        self.assertFalse(self.confirmation.key_expired())

        mock_now.return_value = self.confirmation.created + timedelta(
            minutes=14, seconds=59
        )
        self.assertFalse(self.confirmation.key_expired())

        mock_now.return_value = self.confirmation.created + timedelta(minutes=15)
        self.assertTrue(self.confirmation.key_expired())

    @patch("twitch_osu_bot.users.models.OsuUsernameConfirmation.key_expired")
    def test_confirm(self, mock_expired):
        mock_expired.return_value = True
        self.assertRaises(
            OsuUsernameConfirmation.ConfirmationExpired, self.confirmation.confirm
        )

        mock_expired.return_value = False
        self.assertEqual(self.confirmation.confirm(), self.osu_user)

        self.assertRaises(
            OsuUsernameConfirmation.AlreadyVerified, self.confirmation.confirm
        )
