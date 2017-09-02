# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from allauth.socialaccount.models import SocialApp, SocialToken

import requests


class TwitchApi(object):

    # API endpoints
    API_BASE = 'https://api.twitch.tv/kraken'
    GET_USER = '/'.join((API_BASE, 'user'))
    GET_LIVE_STREAMS = '/'.join((API_BASE, 'streams'))
    GET_STREAM_BY_USER = '/'.join((GET_LIVE_STREAMS, '{channel_id}'))

    def __init__(self, headers={}):
        if headers:
            self.headers = headers
        else:
            try:
                app = SocialApp.objects.get(provider='twitch')
            except SocialApp.DoesNotExist:
                app = SocialApp.objects.create(name='twitch', provider='twitch')
            self.headers = {
                'Accept': 'application/vnd.twitchtv.v5+json',
                'Client-ID': app.client_id,
            }

    @classmethod
    def from_user(cls, user):
        headers = {}
        for token in SocialToken.objects.filter(account__user=user, account__provider='twitch'):
            if token.expires_at is None or token.expires_at > timezone.now():
                headers = {
                    'Client-ID': token.app.client_id,
                    'Authorization': 'OAuth {}'.format(token.token),
                }
        return cls(headers=headers)

    def _parse_timestamps(self, d, keys):
        for k in keys:
            if k in d:
                d[k] = parse_datetime(d[k])

    def _session(self):
        s = requests.Session()
        s.headers.update(self.headers)
        return s

    def get_user(self):
        """Fetch details for the specified user from the Twitch API."""
        with self._session() as s:
            r = s.get(self.GET_USER)
            if r.status_code == 200:
                twitch_user = r.json()
                self._parse_timestamps(twitch_user, ['created_at', 'updated_at'])
                return twitch_user
        return None

    def get_stream_by_user(self, twitch_user, stream_type=None):
        url = self.GET_STREAM_BY_USER.format(channel_id=twitch_user.twitch_id)
        if stream_type in ['live', 'playlist', 'all']:
            params = {'stream_type': stream_type}
        else:
            params = {}
        with self._session() as s:
            r = s.get(url, params=params)
            if r.status_code == 200:
                twitch_stream = r.json()
                return twitch_stream.get('stream')
        return None

    def get_live_streams(self, twitch_users=[], game=None, language=None, stream_type=None):
        url = self.GET_LIVE_STREAMS
        params = {}
        if game:
            params['game'] = game
        if language:
            params['language'] = language
        if stream_type in ['live', 'playlist', 'all']:
            params['stream_type'] = stream_type
        if not twitch_users:
            with self._session() as s:
                r = s.get(url, params=params)
                if r.status_code == 200:
                    twitch_streams = r.json()
                    if 'streams' in twitch_streams:
                        return twitch_streams['streams']
            return []
        else:
            # Twitch will only return a maximum of 100 results, if we need more
            # than that we must combine multiple requests
            params['limit'] = 100
            streams = []
            for channels in [twitch_users[i:i + 100] for i in range(0, len(twitch_users), 100)]:
                params['channel'] = ','.join(map(lambda x: str(x.twitch_id), channels))
                with self._session() as s:
                    r = s.get(url, params=params)
                    if r.status_code == 200:
                        twitch_streams = r.json()
                        if 'streams' in twitch_streams:
                            streams.extend(twitch_streams['streams'])
            return streams
