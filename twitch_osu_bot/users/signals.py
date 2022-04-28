from django.dispatch import Signal

osu_username_confirmed = Signal(providing_args=["request", "osu_username"])
osu_username_unlinked = Signal(providing_args=["request", "user", "username"])
