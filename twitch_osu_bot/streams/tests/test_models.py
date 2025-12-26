# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from ossapi.enums import RankStatus
from test_plus.test import TestCase

from ...users.tests.factories import UserFactory
from ..models import TwitchUser
from .factories import BotOptionsFactory


class TestTwitchUser(TestCase):
    def setUp(self):
        self.user = UserFactory()

    @patch("twitch_osu_bot.streams.models.TwitchApi.from_user")
    def test_update_or_create(self, mock_from_user):
        # example GET_USER response from twitch api docs
        data = {
            "_id": 44322889,
            "bio": "Just a gamer playing games and chatting. :)",
            "created_at": "2013-06-03T19:12:02Z",
            "display_name": "dallas",
            "email": "email-address@provider.com",
            "email_verified": True,
            "logo": "https://static-cdn.jtvnw.net/jtv_user_pictures/dallas-profile_image-1a2c906ee2c35f12-300x300.png",
            "name": "dallas",
            "notifications": {"email": False, "push": True},
            "partnered": False,
            "twitter_connected": False,
            "type": "staff",
            "updated_at": "2016-12-14T01:01:44Z",
        }

        api = MagicMock()
        api.get_user = MagicMock(return_value=data)
        mock_from_user.return_value = api
        self.assertEqual(TwitchUser.update_or_create(self.user).twitch_id, 44322889)


class TestBotOptions(TestCase):
    def setUp(self):
        self.bot_options = BotOptionsFactory()

    def test_allowed_status_list(self):
        self.assertEqual(
            self.bot_options.allowed_status_list,
            [RankStatus.ranked, RankStatus.approved],
        )
