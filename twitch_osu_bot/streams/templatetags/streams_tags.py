# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django import template
from django.template.defaultfilters import stringfilter
from ossapi.enums import RankStatus

register = template.Library()


@register.filter
@stringfilter
def beatmap_status(s):
    return ", ".join(
        [x.name.upper() for x in map(lambda x: RankStatus(int(x)), s.split(","))]
    )
