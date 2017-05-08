# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.db import models
from django.db.models import Q


class TwitchUserManager(models.Manager):

    def enabled_and_verified_q(self):
        return Q(bot_options__enabled=True, user__osu_username__verified=True)

    def all_enabled_and_verified(self):
        return self.filter(self.enabled_and_verified_q())
