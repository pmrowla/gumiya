# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _

from allauth.account.forms import UserForm

from .models import OsuUsername


class SetOsuUsernameForm(UserForm):

    username = forms.CharField(label=_('Osu! username'),
                               max_length=255,
                               required=True)

    def clean_username(self):
        value = self.cleaned_data['username']
        try:
            osu_username = OsuUsername.objects.get(username=value)
            if osu_username.user == self.user:
                raise forms.ValidationError(_('This Osu! username is already linked to your account.'))
            else:
                raise forms.ValidationError(_('This Osu! username is already linked to another account.'))
        except OsuUsername.DoesNotExist:
            pass
        return value

    def save(self, request):
        return OsuUsername.objects.set_username(request,
                                                request.user,
                                                self.cleaned_data['username'],
                                                message=True)
