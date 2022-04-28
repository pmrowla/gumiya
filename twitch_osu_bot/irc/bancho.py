# -*- coding: utf-8 -*-
"""
Gumiya Bancho (osu!) irc3 plugin.
"""
from __future__ import absolute_import, unicode_literals

import irc3
from django.contrib.sites.shortcuts import get_current_site
from gumiyabot.bancho import BaseBanchoPlugin
from irc3.plugins.command import command
from irc3.plugins.cron import cron

from ..users.models import OsuUsername, OsuUsernameConfirmation


# Bancho does not comply with the IRC spec (thanks peppy) so we need to account
# for that or else the irc3 module will not read any data
class BanchoConnection(irc3.IrcConnection):
    """asyncio protocol to handle Bancho connections"""

    def data_received(self, data):
        """Handle data received from Bancho.

        Bancho does not send trailing carriage returns at the end of IRC
        commands (i.e. it ends a command with \n instead of \r\n).
        """
        if not data.endswith(b"\r\n"):
            data = data.rstrip(b"\n") + b"\r\n"
        return super(BanchoConnection, self).data_received(data)


@irc3.plugin
class GumiyaBanchoPlugin(BaseBanchoPlugin):
    def __init__(self, bot):
        super(GumiyaBanchoPlugin, self).__init__(bot)

    @irc3.event(irc3.rfc.CONNECTED)
    def connected(self, **kw):
        self.bot.log.info("[bancho] Connected to bancho as {}".format(self.bot.nick))

    @command(public=False)
    def verify(self, mask, target, args):
        """Verify an osu! account.

        %%verify <verification_code>
        """
        self.bot.log.debug("[bancho] verify {} {} {}".format(mask, target, args))
        username = mask.nick
        key = args.get("<verification_code>")
        self.bot.log.info(
            "[bancho] New verification request from {}: {}".format(username, key)
        )

        try:
            osu_username = OsuUsername.objects.get(username=username)
        except OsuUsername.DoesNotExist:
            self.bot.log.debug("[bancho] - User is not linked to any twitch accounts")
            self.bot.privmsg(
                mask.nick,
                "You must first link your twitch and your osu! accounts at {} "
                "before you can be verified.".format(get_current_site(None)),
            )
            return

        if osu_username.verified:
            self.bot.log.debug("[bancho] - Already verified")
            self.bot.privmsg(mask.nick, "You are already verified.")
            return
        for confirmation in OsuUsernameConfirmation.objects.filter(
            osu_username=osu_username
        ):
            if confirmation.key == key:
                try:
                    confirmation.confirm()
                    self.bot.log.debug("[bancho] - Verification confirmed")
                    msg = "Congratulations, you are now verified."
                except OsuUsernameConfirmation.ConfirmationExpired:
                    self.bot.log.debug("[bancho] - Expired verification code")
                    msg = (
                        "This verification code is expired. "
                        "Please restart the verification process at {}.".format(
                            get_current_site(None)
                        )
                    )
                self.bot.privmsg(mask.nick, msg)
                return
        self.bot.log.debug("[bancho] - invalid verification code")
        self.bot.privmsg(mask.nick, "Invalid verification code.")

    @cron("0 * * * *")
    def prune_confirmations(self):
        """Cleanup expired confirmations."""
        self.bot.log.debug("[bancho] Deleting expired verification requests")
        OsuUsernameConfirmation.objects.delete_expired_confirmations()
