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

from ..streams.models import BotOptions, TwitchUser
from ..utils import TillerinoApi, TwitchApi


class BeatmapValidationError(Exception):

    def __init__(self, reason):
        self.reason = reason


@irc3.plugin
class Twitch:

    def __init__(self, bot):
        self.bot = bot
        self.bancho_queue = self.bot.config.get('bancho_queue')
        self.bancho_nick = self.bot.config.get('bancho_nick')
        self.osu = OsuApi(
            self.bot.config.get('osu_api_key'),
            connector=AHConnector())
        self.twitch = TwitchApi()
        self.tillerino = TillerinoApi(self.bot.config.get('tillerino_api_key'))
        self.joined = set()
        self.twitch_ids = {}
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
    def _get_pp(self, beatmap):
        data = self.tillerino.beatmapinfo(beatmap.beatmap_id)
        if data:
            pp = {}
            for entry in data['ppForAcc']['entry']:
                pp[float(entry['key'])] = float(entry['value'])
            if pp:
                beatmap.pp = pp
                return pp
        beatmap.pp = None
        return None

    def validate_beatmaps(self, beatmaps, options):
        valid_beatmaps = []
        if len(beatmaps) > 1:
            mapset = True
        else:
            mapset = False
        for beatmap in beatmaps:
            if beatmap.approved not in options.allowed_status_list:
                if mapset:
                    reason = 'Rejecting [{}] mapset {} - {} (by {}): Approved status must be one of: {}'.format(
                        beatmap.approved.name.capitalize(),
                        beatmap.artist,
                        beatmap.title,
                        beatmap.creator,
                        ', '.join(map(lambda x: x.name.capitalize(), options.allowed_status_list))
                    )
                else:
                    reason = 'Rejecting [{}] beatmap {} - {} [{}] (by {}): Approved status must be one of: {}'.format(
                        beatmap.approved.name.capitalize(),
                        beatmap.artist,
                        beatmap.title,
                        beatmap.version,
                        beatmap.creator,
                        ', '.join(map(lambda x: x.name.capitalize(), options.allowed_status_list))
                    )
                raise BeatmapValidationError(reason)
            elif beatmap.difficultyrating >= options.beatmap_min_stars \
                    and beatmap.difficultyrating <= options.beatmap_max_stars:
                valid_beatmaps.append(beatmap)
        if not valid_beatmaps:
            if mapset:
                reason = (
                    'Rejecting mapset {} - {} (by {}): '
                    'Must contain at least one beatmap with difficulty in range {:g} to {:g} ★'.format(
                        beatmaps[0].artist,
                        beatmaps[0].title,
                        beatmaps[0].creator,
                        round(options.beatmap_min_stars, 2),
                        round(options.beatmap_max_stars, 2)
                    ))
            else:
                reason = (
                    'Rejecting beatmap {} - {} [{}] (by {}) {:g} ★: '
                    'Difficulty must be in range {:g} ★ to {:g} ★'.format(
                        beatmaps[0].artist,
                        beatmaps[0].title,
                        beatmaps[0].version,
                        beatmaps[0].creator,
                        round(beatmaps[0].difficultyrating, 2),
                        round(options.beatmap_min_stars, 2),
                        round(options.beatmap_max_stars, 2)
                    ))
            raise BeatmapValidationError(reason)
        return valid_beatmaps

    @asyncio.coroutine
    def _beatmap_msg(self, beatmap):
        msg = '[{}] {} - {} [{}] (by {}), ♫ {:g}, ★ {:.2f}'.format(
            beatmap.approved.name.capitalize(),
            beatmap.artist,
            beatmap.title,
            beatmap.version,
            beatmap.creator,
            beatmap.bpm,
            round(beatmap.difficultyrating, 2),
        )
        pp = yield from self._get_pp(beatmap)
        if pp:
            msg = ' | '.join([
                msg,
                '95%: {}pp'.format(round(pp[.95])),
                '98%: {}pp'.format(round(pp[.98])),
                '100%: {}pp'.format(round(pp[1.0])),
            ])
        return msg

    @asyncio.coroutine
    def _request_mapset(self, match, mask, target, options):
        try:
            mapset = yield from self.osu.get_beatmaps(
                beatmapset_id=match.group('mapset_id'),
                include_converted=0)
            if not mapset:
                return (None, None)
            mapset = sorted(mapset, key=lambda x: x.difficultyrating)
        except HTTPError:
            return (None, None)
        try:
            beatmap = self.validate_beatmaps(mapset, options)[-1]
        except BeatmapValidationError as e:
            return (None, e.reason)
        msg = yield from self._beatmap_msg(beatmap)
        return (beatmap, msg)

    @asyncio.coroutine
    def _request_beatmap(self, match, mask, target, options):
        try:
            beatmaps = yield from self.osu.get_beatmaps(
                beatmap_id=match.group('beatmap_id'),
                include_converted=0)
            if not beatmaps:
                return (None, None)
        except HTTPError as e:
            self.bot.log.debug(e)
            return (None, None)
        try:
            beatmap = self.validate_beatmaps(beatmaps, options)[0]
        except BeatmapValidationError as e:
            return (None, e.reason)
        msg = yield from self._beatmap_msg(beatmap)
        return (beatmap, msg)

    @irc3.event(irc3.rfc.PRIVMSG)
    @asyncio.coroutine
    def request_beatmap(self, tags=None, mask=None, target=None, data=None, **kw):
        if not target.is_channel or not data:
            return
        if tags:
            tags = tags.tagdict
            # print(tags)
        options = BotOptions.objects.get(twitch_user__twitch_id=self.twitch_ids[str(target)])
        patterns = [
            (r'https?://osu\.ppy\.sh/b/(?P<beatmap_id>\d+)',
             self._request_beatmap),
            (r'https?://osu\.ppy\.sh/s/(?P<mapset_id>\d+)',
             self._request_mapset),
        ]
        for pattern, callback in patterns:
            m = re.match(pattern, data)
            if m:
                (beatmap, msg) = yield from callback(m, mask, target, options)
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
                    if beatmap.pp:
                        bancho_msg = ' | '.join([
                            bancho_msg,
                            '95%: {}pp'.format(round(beatmap.pp[.95])),
                            '98%: {}pp'.format(round(beatmap.pp[.98])),
                            '100%: {}pp'.format(round(beatmap.pp[1.0])),
                        ])
                    yield from self.bancho_queue.put((self.bancho_nick, bancho_msg))
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
                    twitch_id = stream['channel']['_id']
                    channel = '#{}'.format(name)
                    self.twitch_ids[channel] = twitch_id
                    live.add(channel)
            joins = live.difference(self.joined)
            parts = self.joined.difference(live)
            for channel in joins:
                self.join(channel)
            for channel in parts:
                self.part(channel)
                if channel in self.twitch_ids:
                    del self.twitch_ids[channel]
            yield from asyncio.sleep(30)
