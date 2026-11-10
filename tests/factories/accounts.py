import factory

TEST_PASSWORD = 'una-contrasena-de-prueba'


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'accounts.User'

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@mail.com')
    password = factory.django.Password(TEST_PASSWORD)
