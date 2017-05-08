# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django import template
from django.template.defaultfilters import stringfilter

from osuapi.enums import BeatmapStatus

register = template.Library()


@register.filter
@stringfilter
def beatmap_status(s):
    return ', '.join([x.name.upper() for x in map(lambda x: BeatmapStatus(int(x)), s.split(','))])
