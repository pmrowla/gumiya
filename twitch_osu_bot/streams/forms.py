# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django import forms
from django.utils.translation import gettext_lazy as _
from osuapi.enums import BeatmapStatus

from .models import BotOptions


class BotOptionsForm(forms.ModelForm):
    enabled = forms.TypedChoiceField(
        label=_("Enable the bot on your twitch channel"),
        coerce=lambda x: bool(int(x)),
        choices=[(1, "Yes"), (0, "No")],
        required=True,
    )
    subs_only = forms.TypedChoiceField(
        label=_("Restrict bot functions to subscribers only"),
        coerce=lambda x: bool(int(x)),
        choices=[(1, "Yes"), (0, "No")],
        required=False,
    )

    beatmap_allowed_status = forms.TypedMultipleChoiceField(
        label=("Allowed statuses for beatmap requests"),
        choices=[(x.value, x.name.upper()) for x in BeatmapStatus],
        coerce=lambda x: int(x),
        required=True,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = BotOptions
        fields = [
            "enabled",
            "subs_only",
            "beatmap_allowed_status",
            "beatmap_min_stars",
            "beatmap_max_stars",
        ]
        labels = {
            "beatmap_min_stars": _("Minimum allowed star rating for beatmap requests"),
            "beatmap_max_stars": _("Maximum allowed star rating for beatmap requests"),
        }

    def __init__(self, *args, **kwargs):
        super(BotOptionsForm, self).__init__(*args, **kwargs)
        self.initial["enabled"] = int(self.initial["enabled"])
        self.initial["subs_only"] = int(self.initial["subs_only"])

    def clean_beatmap_allowed_status(self):
        return ",".join([str(x) for x in self.cleaned_data["beatmap_allowed_status"]])

    def _clean_stars(self):
        min_stars = self.cleaned_data["beatmap_min_stars"]
        max_stars = self.cleaned_data["beatmap_max_stars"]
        if min_stars >= max_stars:
            raise forms.ValidationError(
                _("Minimum star rating must be less than maximum star rating")
            )

    def clean_beatmap_min_stars(self):
        if "beatmap_max_stars" in self.cleaned_data:
            self._clean_stars()
        return self.cleaned_data["beatmap_min_stars"]

    def clean_beatmap_max_stars(self):
        if "beatmap_min_stars" in self.cleaned_data:
            self._clean_stars()
        return self.cleaned_data["beatmap_max_stars"]
