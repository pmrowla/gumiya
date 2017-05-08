# -*- coding: utf-8 -*-
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.models import AbstractUser
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from . import signals
from .managers import OsuUsernameManager, OsuUsernameConfirmationManager


@python_2_unicode_compatible
class User(AbstractUser):

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse('users:detail', kwargs={'username': self.username})


@python_2_unicode_compatible
class OsuUsername(models.Model):

    user = models.OneToOneField(User,
                                verbose_name=_('user'),
                                related_name='osu_username',
                                on_delete=models.CASCADE)
    username = models.CharField(_('osu! username'),
                                unique=True,
                                max_length=255)
    verified = models.BooleanField(_('verified'), default=False)

    objects = OsuUsernameManager()

    def __str__(self):
        return '{} ({})'.format(self.username, self.user)

    def send_confirmation(self, request=None, message=False):
        confirmation = OsuUsernameConfirmation.create(self)
        if message:
            msg = ('To verify your account, PM the following message in game to '
                   '{} (verification key will expire in 15 minutes): '
                   '!verify {}'.format('pmrowla', confirmation.key))
            messages.info(request, msg)
        return confirmation

    def change(self, request, new_username, message=False):
        try:
            atomic_transaction = transaction.atomic
        except AttributeError:
            atomic_transaction = transaction.commit_on_success

        with atomic_transaction():
            self.username = new_username
            self.verified = False
            self.save()
            self.send_confirmation(request, message=message)


@python_2_unicode_compatible
class OsuUsernameConfirmation(models.Model):

    osu_username = models.ForeignKey(OsuUsername,
                                     verbose_name=_('osu! username'),
                                     on_delete=models.CASCADE)
    created = models.DateTimeField(_('created'), auto_now_add=True)
    key = models.CharField(_('key'), max_length=12, unique=True)

    objects = OsuUsernameConfirmationManager()

    def __str__(self):
        return 'confirmation for {}'.format(self.osu_username)

    @classmethod
    def create(cls, osu_username):
        key = get_random_string(12).lower()
        return cls._default_manager.create(osu_username=osu_username, key=key)

    def key_expired(self):
        expiration_date = self.created + timedelta(minutes=15)
        return expiration_date <= timezone.now()
    key_expired.boolean = True

    def confirm(self, request=None):
        if self.key_expired():
            raise self.ConfirmationExpired
        elif self.osu_username.verified:
            raise self.AlreadyVerified
        else:
            osu_username = self.osu_username
            osu_username.verified = True
            osu_username.save()
            signals.osu_username_confirmed.send(sender=self.__class__,
                                                request=request,
                                                osu_username=osu_username)
            return osu_username

    class AlreadyVerified(Exception):
        pass

    class ConfirmationExpired(Exception):
        pass
