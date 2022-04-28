# -*- coding: utf-8 -*-
import asyncio

import irc3
from django.conf import settings
from django.core.management.base import BaseCommand
from gumiyabot.bancho import BanchoConnection


class Command(BaseCommand):

    help = "Run the twitch and bancho IRC bots."

    def handle(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        bancho_queue = asyncio.Queue(loop=loop)

        config_common = {
            "irc3.plugins.command": {
                "hash": "#",
                "cmd": "!",
                "guard": "irc3.plugins.command.mask_based_policy",
            },
            "irc3.plugins.command.masks": {
                "hash": "#",
                "*": "view",
            },
        }
        if settings.DEBUG:
            config_common["debug"] = True

        twitch_config = dict(
            host="irc.chat.twitch.tv",
            port=6667,
            includes=[
                "irc3.plugins.core",
                "irc3.plugins.autocommand",
                "irc3.plugins.command",
                "irc3.plugins.cron",
                "irc3.plugins.log",
                "twitch_osu_bot.irc.twitch",
            ],
            autocommands=[
                "CAP REQ :twitch.tv/membership",
                "CAP REQ :twitch.tv/commands",
                "CAP REQ :twitch.tv/tags",
            ],
            nick=settings.TWITCH_USERNAME,
            password=settings.TWITCH_PASSWORD,
            osu_api_key=settings.OSU_API_KEY,
            tillerino_api_key=settings.TILLERINO_API_KEY,
            bancho_nick=settings.BANCHO_USERNAME,
        )
        twitch_config.update(config_common)

        if settings.DEBUG:
            twitch_config["debug_username"] = settings.DEBUG_USERNAME

        bancho_config = dict(
            host="irc.ppy.sh",
            port=6667,
            includes=[
                "irc3.plugins.core",
                "irc3.plugins.command",
                "irc3.plugins.cron",
                "irc3.plugins.log",
                "twitch_osu_bot.irc.bancho",
            ],
            nick=settings.BANCHO_USERNAME,
            password=settings.BANCHO_PASSWORD,
        )
        bancho_config.update(config_common)
        twitch_bot = irc3.IrcBot(loop=loop, bancho_queue=bancho_queue, **twitch_config)
        twitch_bot.run(forever=False)

        bancho_bot = irc3.IrcBot(
            loop=loop,
            bancho_queue=bancho_queue,
            connection=BanchoConnection,
            **bancho_config
        )
        bancho_bot.run(forever=False)

        loop.run_forever()
