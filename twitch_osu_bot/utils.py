# -*- coding: utf-8 -*-
import logging

import requests
from allauth.socialaccount.models import SocialApp, SocialToken
from django.utils import timezone
from django.utils.dateparse import parse_datetime

logger = logging.getLogger(__name__)


class TwitchApi(object):
    # API endpoints
    API_BASE = "https://api.twitch.tv/helix"
    GET_USERS = "/".join((API_BASE, "users"))
    GET_LIVE_STREAMS = "/".join((API_BASE, "streams"))

    def __init__(self, headers={}):
        if headers:
            self.headers = headers
        else:
            try:
                app = SocialApp.objects.get(provider="twitch")
            except SocialApp.DoesNotExist:
                app = SocialApp.objects.create(name="twitch", provider="twitch")
            self.headers = {
                "Client-ID": app.client_id,
            }
        self.headers["Accept"] = "application/vnd.twitchtv.v5+json"
        self._app_token = None

    @property
    def app_token(self):
        if self._app_token is None:
            app = SocialApp.objects.get(provider="twitch")
            url = "https://id.twitch.tv/oauth2/token"
            params = {
                "client_id": app.client_id,
                "client_secret": app.secret,
                "grant_type": "client_credentials",
            }
            with self._session() as s:
                r = s.post(url, params=params)
                if r.status_code == 200:
                    self._app_token = r.json().get("access_token")
        return self._app_token

    @classmethod
    def from_user(cls, user):
        headers = {}
        for token in SocialToken.objects.filter(
            account__user=user, account__provider="twitch"
        ):
            if token.expires_at is None or token.expires_at > timezone.now():
                headers = {
                    "Client-ID": token.app.client_id,
                    "Authorization": "Bearer {}".format(token.token),
                }
        return cls(headers=headers)

    def _parse_timestamps(self, d, keys):
        for k in keys:
            if k in d:
                d[k] = parse_datetime(d[k])

    def _session(self, headers={}):
        s = requests.Session()
        s.headers.update(self.headers)
        s.headers.update(headers)
        return s

    def get_user(self):
        """Fetch details for the specified user from the Twitch API."""
        with self._session() as s:
            r = s.get(self.GET_USERS)
            if r.status_code == 200:
                twitch_user = r.json().get("data", [])[0]
                self._parse_timestamps(twitch_user, ["created_at", "updated_at"])
                return twitch_user
        return None

    def get_live_streams(self, twitch_users=[], game_id=None, language=None):
        url = self.GET_LIVE_STREAMS
        params = {}
        if game_id:
            params["game_id"] = game_id
        if language:
            params["language"] = language
        token = self.app_token
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        if not twitch_users:
            with self._session(headers=headers) as s:
                r = s.get(url, params=params)
                if r.status_code == 200:
                    return r.json().get("data", [])
            return []
        else:
            # Twitch will only return a maximum of 100 results, if we need more
            # than that we must combine multiple requests
            query = "first=100&"
            streams = []
            for channels in [
                twitch_users[i : i + 100] for i in range(0, len(twitch_users), 100)
            ]:
                query += "&".join(
                    f"user_id={channel.twitch_id}" for channel in channels
                )
                with self._session(headers=headers) as s:
                    r = s.get(f"{url}?{query}")
                    if r.status_code == 200:
                        streams.extend(r.json().get("data", []))
            return streams
