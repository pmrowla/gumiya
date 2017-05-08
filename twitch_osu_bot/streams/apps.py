from django.apps import AppConfig


class StreamsConfig(AppConfig):
    name = 'twitch_osu_bot.streams'
    verbose_name = "Twitch Streams"

    def ready(self):
        pass
