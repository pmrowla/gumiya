# -*- coding: utf-8 -*-
"""
twitch_osu_bot Twitch chat irc3 plugin.
"""
import asyncio

import irc3
from asgiref.sync import sync_to_async
from gumiyabot.twitch import BaseTwitchPlugin, BeatmapValidationError
from gumiyabot.utils import TillerinoApi
from irc3.plugins.command import command
from ossapi import OssapiAsync
from requests.exceptions import RequestException

from ..streams.models import BotOptions, TwitchUser
from ..utils import TwitchApi


@irc3.plugin
class GumiyaTwitchPlugin(BaseTwitchPlugin):
    def __init__(self, bot):
        self.bot = bot
        self.bancho_queue = self.bot.config.get("bancho_queue")
        self.bancho_nick = self.bot.config.get("bancho_nick")
        self.osu = OssapiAsync(
            self.bot.config.get("osu_client_id"),
            self.bot.config.get("osu_client_secret"),
            token_directory=self.bot.config.get("osu_token_directory")
        )
        self.twitch = TwitchApi()
        self.tillerino = TillerinoApi(self.bot.config.get("tillerino_api_key"))
        self.joined = set()
        self.twitch_ids = {}
        self.osu_nicks = {}
        self.finished = False

    def server_ready(self):
        self.finished = False
        asyncio.ensure_future(self.join_live_channels())

    def connection_lost(self):
        self.finished = True

    @irc3.event(irc3.rfc.CONNECTED)
    def connected(self, **kw):
        # Override connected() since we don't use default twitch_channel
        self.bot.log.info("[twitch] Connected to twitch as {}".format(self.bot.nick))

    def validate_beatmaps(self, beatmaps, mapset, **kwargs):
        valid_beatmaps = []
        for beatmap, diff in beatmaps:
            if beatmap.approved not in options.allowed_status_list:
                if len(beatmaps) > 1:
                    reason = "Rejecting [{}] mapset {} - {} (by {}): Approved status must be one of: {}".format(
                        beatmap.status.name.capitalize(),
                        mapset.artist,
                        mapset.title,
                        mapset.creator,
                        ", ".join(
                            map(
                                lambda x: x.name.capitalize(),
                                options.allowed_status_list,
                            )
                        ),
                    )
                else:
                    reason = "Rejecting [{}] beatmap {} - {} [{}] (by {}): Approved status must be one of: {}".format(
                        beatmap.status.name.capitalize(),
                        mapset.artist,
                        mapset.title,
                        mapset.version,
                        mapset.creator,
                        ", ".join(
                            map(
                                lambda x: x.name.capitalize(),
                                options.allowed_status_list,
                            )
                        ),
                    )
                raise BeatmapValidationError(reason)
            elif (
                diff.star_rating >= options.beatmap_min_stars
                and diff.star_rating <= options.beatmap_max_stars
            ):
                valid_beatmaps.append(beatmap)
        if not valid_beatmaps:
            beatmap, diff = beatmaps[0]
            if len(beatmaps) > 1:
                reason = (
                    "Rejecting mapset {} - {} (by {}): "
                    "Must contain at least one beatmap with difficulty in range {:g} to {:g} ★".format(
                        mapset.artist,
                        mapset.title,
                        mapset.creator,
                        round(options.beatmap_min_stars, 2),
                        round(options.beatmap_max_stars, 2),
                    )
                )
            else:
                reason = (
                    "Rejecting beatmap {} - {} [{}] (by {}) {:g} ★: "
                    "Difficulty must be in range {:g} ★ to {:g} ★".format(
                        mapset.artist,
                        mapset.title,
                        beatmap.version,
                        mapset.creator,
                        round(diff.star_rating, 2),
                        round(options.beatmap_min_stars, 2),
                        round(options.beatmap_max_stars, 2),
                    )
                )
            raise BeatmapValidationError(reason)
        return valid_beatmaps

    @irc3.event(irc3.rfc.PRIVMSG)
    async def request_beatmap(
        self, tags=None, mask=None, target=None, data=None, **kwargs
    ):
        if not target.is_channel or not data:
            return
        try:
            options = await sync_to_async(BotOptions.objects.get)(
                twitch_user__twitch_id=self.twitch_ids[str(target)]
            )
        except BotOptions.DoesNotExist:
            return
        if options.subs_only:
            self.bot.log.debug("[twitch] subs only mode is on")
            if not tags:
                self.bot.log.warn(
                    "[twitch] no IRCv3 tags in PRIVMSG, cannot check for subs only"
                )
                return
            if not self._is_sub(tags.tagdict):
                return
            self.bot.log.debug("[twitch] - {} is a sub or mod".format(mask.nick))
        return await super().request_beatmap(
            tags=tags,
            mask=mask,
            target=target,
            data=data,
            options=options,
            bancho_target=self.osu_nicks[str(target)],
            **kwargs,
        )

    def join(self, channel):
        self.bot.log.info("[twitch] Trying to join channel {}".format(channel))
        self.bot.join(channel)
        self.joined.add(channel)

    def part(self, channel):
        self.bot.log.info("[twitch] Leaving channel {}".format(channel))
        self.bot.part(channel)
        if channel in self.joined:
            self.joined.remove(channel)

    async def join_live_channels(self):
        while not self.finished:
            self.bot.log.debug("[twitch] Checking for live streams")
            live = set()
            twitch_users = TwitchUser.objects.all_enabled_and_verified()
            if await sync_to_async(twitch_users.exists)():
                try:
                    live_streams = await sync_to_async(self.twitch.get_live_streams)(
                        twitch_users=twitch_users
                    )
                except RequestException as e:
                    self.bot.log.warn(
                        f"[twitch] error fetching live streams from twitch: {e}"
                    )
                    live_streams = []
                for stream in live_streams:
                    if stream and stream["game_name"] == "osu!":
                        name = stream["user_login"]
                        twitch_id = stream["user_id"]
                        channel = "#{}".format(name)
                        self.twitch_ids[channel] = twitch_id
                        osu_username = await sync_to_async(
                            TwitchUser.osu_username_for_twitch_id
                        )(twitch_id)
                        self.osu_nicks[channel] = osu_username.username
                        live.add(channel)
            if self.bot.config.get("debug"):
                debug_username = self.bot.config.get("debug_username")
                if debug_username:
                    try:
                        twitch_user = await sync_to_async(TwitchUser.objects.get)(
                            user__username=debug_username
                        )
                        osu_username = await sync_to_async(
                            TwitchUser.osu_username_for_twitch_id
                        )(twitch_user.twitch_id)
                        if osu_username:
                            channel = "#{}".format(debug_username)
                            self.twitch_ids[channel] = twitch_user.twitch_id
                            self.osu_nicks[channel] = osu_username.username
                            live.add(channel)
                    except TwitchUser.DoesNotExist:
                        self.bot.log.debug("[twitch] debug user does not exist")
            joins = live.difference(self.joined)
            parts = self.joined.difference(live)
            for channel in joins:
                self.join(channel)
            for channel in parts:
                self.part(channel)
                if channel in self.twitch_ids:
                    del self.twitch_ids[channel]
                if channel in self.osu_nicks:
                    del self.osu_nicks[channel]
            await asyncio.sleep(30)

    @command
    async def stats(self, mask, target, args):
        """Check stats for an osu! player

        %%stats [<username>]...
        """
        return await super().stats(
            mask, target, args, default_user=self.osu_nicks[str(target)]
        )
