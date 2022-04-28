from django.apps import AppConfig


class IrcConfig(AppConfig):
    name = "twitch_osu_bot.irc"
    verbose_name = "IRC"

    def ready(self):
        """Override this to put in:
        Users system checks
        Users signal registration
        """
        pass
