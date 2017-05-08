# -*- coding: utf-8 -*-
"""
twitch_osu_bot Bancho (osu!) irc3 plugin.
"""
from __future__ import absolute_import, unicode_literals

import asyncio

import irc3
from irc3.plugins.command import command
from irc3.plugins.cron import cron

from django.contrib.sites.shortcuts import get_current_site

from ..users.models import OsuUsername, OsuUsernameConfirmation


@irc3.plugin
class Bancho:

    def __init__(self, bot):
        self.bot = bot
        self.bancho_queue = self.bot.config.get('bancho_queue')
        asyncio.ensure_future(self.get_bancho_msg())

    @irc3.event(irc3.rfc.CONNECTED)
    def connected(self, **kw):
        self.bot.log.info('Connected to bancho as {}'.format(self.bot.nick))

    @asyncio.coroutine
    def get_bancho_msg(self):
        while True:
            (target, msg) = yield from self.bancho_queue.get()
            self.bot.privmsg(target, msg)

    @command(public=False)
    def verify(self, mask, target, args):
        """Verify an osu! account.

            %%verify <verification_code>
        """
        self.bot.log.debug('verify {} {} {}'.format(mask, target, args))
        username = mask.nick
        key = args.get('<verification_code>')
        self.bot.log.debug('New verification request from {}: {}'.format(username, key))

        try:
            osu_username = OsuUsername.objects.get(username=username)
        except OsuUsername.DoesNotExist:
            self.bot.log.debug(' - User is not linked to any twitch accounts')
            self.bot.privmsg(mask.nick,
                             'You must first link your twitch and your osu! accounts at {} '
                             'before you can be verified.'.format(get_current_site(None)))
            return

        if osu_username.verified:
            self.bot.log.debug(' - Already verified')
            self.bot.privmsg(mask.nick, 'You are already verified.')
            return
        for confirmation in OsuUsernameConfirmation.objects.filter(osu_username=osu_username):
            if confirmation.key == key:
                try:
                    confirmation.confirm()
                    self.bot.log.debug(' - Verification confirmed')
                    msg = 'Congratulations, you are now verified.'
                except OsuUsernameConfirmation.ConfirmationExpired:
                    self.bot.log.debug(' - Expired verification code')
                    msg = ('This verification code is expired. '
                           'Please restart the verification process at {}.'.format(get_current_site(None)))
                self.bot.privmsg(mask.nick, msg)
                return
        self.bot.log.debug(' - invalid verification code')
        self.bot.privmsg(mask.nick, 'Invalid verification code.')

    @cron('0 * * * *')
    def prune_confirmations(self):
        """Cleanup expired confirmations."""
        self.bot.log.debug('Deleting expired verification requests')
        OsuUsernameConfirmation.objects.delete_expired_confirmations()
