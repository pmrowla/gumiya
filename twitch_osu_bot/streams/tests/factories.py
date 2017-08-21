import factory

from ...users.tests.factories import UserFactory


class TwitchUserFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    twitch_id = factory.Sequence(lambda n: n)

    class Meta:
        model = 'streams.TwitchUser'


class BotOptionsFactory(factory.django.DjangoModelFactory):
    twitch_user = factory.SubFactory(TwitchUserFactory)

    class Meta:
        model = 'streams.BotOptions'
