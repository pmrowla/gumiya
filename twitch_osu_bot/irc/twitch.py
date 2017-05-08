# -*- coding: utf-8 -*-
"""
twitch_osu_bot Twitch chat irc3 plugin.
"""
from __future__ import unicode_literals

import asyncio
import re

import irc3

from osuapi import OsuApi, AHConnector
from osuapi.errors import HTTPError

from ..streams.models import TwitchUser
from ..utils import TwitchApi


@irc3.plugin
class Twitch:

    def __init__(self, bot):
        self.bot = bot
        self.bancho_queue = self.bot.config.get('bancho_queue')
        self.osu = OsuApi(
            self.bot.config.get('osu_api_key'),
            connector=AHConnector())
        self.twitch = TwitchApi()
        self.joined = set()
        self.finished = False

    def server_ready(self):
        self.finished = False
        asyncio.ensure_future(self.join_live_channels())

    def connection_lost(self):
        self.finished = True

    @irc3.event(irc3.rfc.CONNECTED)
    def connected(self, **kw):
        self.bot.log.info('Connected to twitch as {}'.format(self.bot.nick))

    @asyncio.coroutine
    def _request_mapset(self, match, mask, target):
        try:
            mapset = yield from self.osu.get_beatmaps(
                beatmapset_id=match.group('mapset_id'),
                include_converted=0)
            if not mapset:
                return (None, None)
        except HTTPError:
            return (None, None)
        beatmap = sorted(
            mapset, key=lambda x: x.difficultyrating)[-1]
        msg = '[{}] {} - {} (by {}), ♫ {:g}, hardest diff [{}] ★ {:.2f}'.format(
            beatmap.approved.name.capitalize(),
            beatmap.artist,
            beatmap.title,
            beatmap.creator,
            beatmap.bpm,
            beatmap.version,
            round(beatmap.difficultyrating, 2),
        )
        return (beatmap, msg)

    @asyncio.coroutine
    def _request_beatmap(self, match, mask, target):
        try:
            beatmap = yield from self.osu.get_beatmaps(
                beatmap_id=match.group('beatmap_id'),
                include_converted=0)
            if not beatmap:
                return (None, None)
        except HTTPError as e:
            self.bot.log.debug(e)
            return (None, None)
        beatmap = beatmap[0]
        msg = '[{}] {} - {} [{}] (by {}), ♫ {:g}, ★ {:.2f}'.format(
            beatmap.approved.name.capitalize(),
            beatmap.artist,
            beatmap.title,
            beatmap.version,
            beatmap.creator,
            beatmap.bpm,
            round(beatmap.difficultyrating, 2),
        )
        return (beatmap, msg)

    @irc3.event(irc3.rfc.PRIVMSG)
    @asyncio.coroutine
    def request_beatmap(self, tags=None, mask=None, target=None, data=None, **kw):
        if not target.is_channel or not data:
            return
        if tags:
            tags = tags.tagdict
            print(tags)
        patterns = [
            (r'https?://osu\.ppy\.sh/b/(?P<beatmap_id>\d+)',
             self._request_beatmap),
            (r'https?://osu\.ppy\.sh/s/(?P<mapset_id>\d+)',
             self._request_mapset),
        ]
        for pattern, callback in patterns:
            m = re.match(pattern, data)
            if m:
                (beatmap, msg) = yield from callback(m, mask, target)
                if beatmap:
                    m, s = divmod(beatmap.total_length, 60)
                    bancho_msg = ' '.join([
                        '{} >'.format(mask.nick),
                        '[http://osu.ppy.sh/b/{} {} - {} [{}]]'.format(
                            beatmap.beatmap_id,
                            beatmap.artist,
                            beatmap.title,
                            beatmap.version,
                        ),
                        '{}:{:02d} ★ {:.2f} ♫ {:g} AR{:g} OD{:g}'.format(
                            m, s,
                            round(beatmap.difficultyrating, 2),
                            beatmap.bpm,
                            round(beatmap.diff_approach, 1),
                            round(beatmap.diff_overall, 1),
                        ),
                    ])
                    yield from self.bancho_queue.put(('pmrowla', bancho_msg))
                if msg:
                    self.bot.privmsg(target, msg)
                break

    def join(self, channel):
        self.bot.log.info('Trying to join channel {}'.format(channel))
        self.bot.join(channel)
        self.joined.add(channel)

    def part(self, channel):
        self.bot.log.info('Leaving channel {}'.format(channel))
        self.bot.part(channel)
        if channel in self.joined:
            self.joined.remove(channel)

    @asyncio.coroutine
    def join_live_channels(self):
        while not self.finished:
            self.bot.log.debug('Checking for live streams')
            live = set()
            twitch_users = TwitchUser.objects.all_enabled_and_verified()
            for stream in self.twitch.get_live_streams(twitch_users=twitch_users):
                if stream:
                    name = stream['channel']['name']
                    live.add('#{}'.format(name))
            joins = live.difference(self.joined)
            parts = self.joined.difference(live)
            for channel in joins:
                self.join(channel)
            for channel in parts:
                self.part(channel)
            yield from asyncio.sleep(30)
