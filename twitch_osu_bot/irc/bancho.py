# -*- coding: utf-8 -*-
"""
Gumiya Bancho (osu!) irc3 plugin.
"""
import irc3
from asgiref.sync import sync_to_async
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


def _format_site():
    site = str(get_current_site(None))
    return f"[https://{site} {site}]"


@irc3.plugin
class GumiyaBanchoPlugin(BaseBanchoPlugin):
    def __init__(self, bot):
        super(GumiyaBanchoPlugin, self).__init__(bot)

    @irc3.event(irc3.rfc.CONNECTED)
    def connected(self, **kw):
        self.bot.log.info(f"[bancho] Connected to bancho as {self.bot.nick}")

    @command(public=False)
    async def verify(self, mask, target, args):
        """Verify an osu! account.

        %%verify <verification_code>
        """
        username = mask.nick
        key = args.get("<verification_code>")
        self.bot.log.info(f"[bancho] New verification request from {username}: {key}")

        try:
            osu_username = await sync_to_async(OsuUsername.objects.get)(
                username=username
            )
        except OsuUsername.DoesNotExist:
            self.bot.log.debug("[bancho] - User is not linked to any twitch accounts")
            site = await sync_to_async(_format_site)()
            self.bot.privmsg(
                mask.nick,
                f"You must first link your twitch and your osu! accounts at {site} "
                "before you can be verified.",
            )
            return

        if osu_username.verified:
            self.bot.log.debug("[bancho] - Already verified")
            self.bot.privmsg(mask.nick, "You are already verified.")
            return
        try:
            confirmation = await sync_to_async(OsuUsernameConfirmation.objects.get)(
                osu_username=osu_username, key=key
            )
        except OsuUsernameConfirmation.DoesNotExist:
            self.bot.log.debug("[bancho] - invalid verification code")
            self.bot.privmsg(mask.nick, "Invalid verification code.")
            return
        try:
            await sync_to_async(confirmation.confirm)()
            self.bot.log.debug("[bancho] - Verification confirmed")
            msg = "Congratulations, you are now verified."
        except OsuUsernameConfirmation.ConfirmationExpired:
            self.bot.log.debug("[bancho] - Expired verification code")
            site = await sync_to_async(_format_site)()
            msg = (
                "This verification code is expired. "
                f"Please restart the verification process at {site}."
            )
        self.bot.privmsg(mask.nick, msg)

    @cron("0 * * * *")
    async def prune_confirmations(self):
        """Cleanup expired confirmations."""
        self.bot.log.debug("[bancho] Deleting expired verification requests")
        await sync_to_async(
            OsuUsernameConfirmation.objects.delete_expired_confirmations
        )()
