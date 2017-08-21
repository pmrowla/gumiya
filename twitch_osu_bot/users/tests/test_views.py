from unittest.mock import patch, MagicMock

from django.test import RequestFactory

from test_plus.test import TestCase

from ..views import (
    OsuUsernameView,
    UserDetailView,
    UserRedirectView,
)


class BaseUserTestCase(TestCase):

    def setUp(self):
        self.user = self.make_user()
        self.factory = RequestFactory()


class TestUserDetailView(BaseUserTestCase):

    def setUp(self):
        # call BaseUserTestCase.setUp()
        super(TestUserDetailView, self).setUp()
        # Instantiate the view directly. Never do this outside a test!
        self.view = UserDetailView()
        # Generate a fake request
        request = self.factory.get('/fake-url')
        # Attach the user to the request
        request.user = self.user
        # Attach the request to the view
        self.view.request = request

    @patch('twitch_osu_bot.streams.models.TwitchUser.update_or_create')
    @patch('twitch_osu_bot.streams.models.BotOptions.objects.get_or_create')
    def test_get_object(self, mock_bot_options, mock_twitch_user):
        mock_twitch_user.return_value = MagicMock()
        # Expect: self.user, as that is the request's user object
        self.assertEqual(
            self.view.get_object(),
            self.user
        )
        mock_twitch_user.assert_called_with(self.user)
        mock_bot_options.assert_called_with(twitch_user=mock_twitch_user.return_value)


class TestUserRedirectView(BaseUserTestCase):

    def test_get_redirect_url(self):
        # Instantiate the view directly. Never do this outside a test!
        view = UserRedirectView()
        # Generate a fake request
        request = self.factory.get('/fake-url')
        # Attach the user to the request
        request.user = self.user
        # Attach the request to the view
        view.request = request
        self.assertEqual(
            view.get_redirect_url(),
            '/profile/'
        )


class TestOsuUsernameView(BaseUserTestCase):

    def setUp(self):
        # call BaseUserTestCase.setUp()
        super(TestOsuUsernameView, self).setUp()
        # Instantiate the view directly. Never do this outside a test!
        self.view = OsuUsernameView()
        # Generate a fake request
        request = self.factory.get('/fake-url')
        # Attach the user to the request
        request.user = self.user
        # Attach the request to the view
        self.view.request = request

    def test_get_success_url(self):
        # Expect: '/users/testuser/', as that is the default username for
        #   self.make_user()
        self.assertEqual(
            self.view.get_success_url(),
            '/profile/'
        )
