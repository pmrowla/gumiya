# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic.edit import UpdateView

from .forms import BotOptionsForm
from .models import BotOptions


class BotOptionsView(LoginRequiredMixin, UpdateView):
    model = BotOptions
    template_name = "streams/bot_options_form.html"
    form_class = BotOptionsForm

    def get_success_url(self):
        return reverse("users:detail")

    def get_object(self):
        return BotOptions.objects.get(twitch_user__user=self.request.user)
