# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import re

from django.db import models
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator)
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from osuapi.enums import BeatmapStatus

from ..utils import TwitchApi
from .managers import TwitchUserManager

from ..users.models import OsuUsername, User


@python_2_unicode_compatible
class TwitchUser(models.Model):

    user = models.OneToOneField(User,
                                verbose_name=_('user'),
                                related_name='twitch_user',
                                on_delete=models.CASCADE)
    twitch_id = models.IntegerField(_('Twitch user ID'),
                                    unique=True)
    logo = models.URLField(_('Twitch logo URL'), default='')
    updated = models.DateTimeField(_('last updated'), auto_now=True)
    objects = TwitchUserManager()

    @classmethod
    def update_or_create(cls, user):
        """Create or update TwitchUser from Twitch API."""
        api = TwitchApi.from_user(user)
        data = api.get_user()
        if not data:
            return None
        try:
            twitch_user = cls.objects.get(user=user, twitch_id=data['_id'])
        except cls.DoesNotExist:
            twitch_user = cls(user=user, twitch_id=data['_id'])
        if twitch_user.user.username != data['display_name']:
            twitch_user.user.username = data['display_name']
            twitch_user.user.save()
        if twitch_user.logo != data['logo']:
            twitch_user.logo = data['logo']
            twitch_user.save()
        return twitch_user

    @classmethod
    def osu_username_for_twitch_id(cls, twitch_id):
        try:
            twitch_user = TwitchUser.objects.get(twitch_id=twitch_id)
            osu_username = OsuUsername.objects.get(user=twitch_user.user)
            return osu_username
        except (TwitchUser.DoesNotExist, OsuUsername.DoesNotExist):
            pass
        return None


@python_2_unicode_compatible
class BotOptions(models.Model):

    twitch_user = models.OneToOneField(TwitchUser,
                                       verbose_name=_('bot options'),
                                       related_name='bot_options',
                                       on_delete=models.CASCADE)
    enabled = models.BooleanField(_('bot enabled'), default=False)
    subs_only = models.BooleanField(_('subscriber only mode'), default=False)

    beatmap_allowed_status = models.CharField(
        _('allowed beatmap status for requests'),
        validators=[
            RegexValidator(re.compile(r'^([-\d,])+$'), _(u'Enter only integers separated by commas.'), 'invalid'),
        ],
        default=','.join([str(BeatmapStatus.ranked.value), str(BeatmapStatus.approved.value)]),
        max_length=64)
    beatmap_min_stars = models.FloatField(
        _('minimum allowed stars for beatmap requests'),
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        default=0.0)
    beatmap_max_stars = models.FloatField(
        _('maximum allowed stars for beatmap requests'),
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        default=10.0)

    @property
    def allowed_status_list(self):
        return [BeatmapStatus(int(x)) for x in self.beatmap_allowed_status.split(',')]
