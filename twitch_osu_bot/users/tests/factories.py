import factory


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: 'user-{0}'.format(n))
    email = factory.Sequence(lambda n: 'user-{0}@example.com'.format(n))
    password = factory.PostGenerationMethodCall('set_password', 'password')

    class Meta:
        model = 'users.User'
        django_get_or_create = ('username', )


class OsuUsernameFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    username = factory.Sequence(lambda n: 'osu-user-{}'.format(n))

    class Meta:
        model = 'users.OsuUsername'
