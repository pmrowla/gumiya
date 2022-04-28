from datetime import timedelta

from django.db import models
from django.db.models import Q
from django.utils import timezone


class OsuUsernameManager(models.Manager):
    def set_username(self, request, user, username, message=False):
        try:
            osu_username = self.get(user=user)
            if osu_username.username != username:
                osu_username.change(request, username, message=message)
        except self.model.DoesNotExist:
            osu_username = self.create(user=user, username=username)
            osu_username.send_confirmation(request, message=message)
        return osu_username


class OsuUsernameConfirmationManager(models.Manager):
    def all_expired(self):
        return self.filter(self.expired_q())

    def all_valid(self):
        return self.exclude(self.expired_q())

    def expired_q(self):
        created_threshold = timezone.now() - timedelta(minutes=15)
        return Q(created__lt=created_threshold)

    def delete_expired_confirmations(self):
        self.all_expired().delete()
