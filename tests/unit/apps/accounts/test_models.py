import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.accounts.models import User
from tests.factories.accounts import UserFactory

pytestmark = pytest.mark.django_db


def test_stores_the_email_in_lowercase():
    user = User.objects.create_user(username='rosa', email='Rosa.Quispe@Mail.COM')

    assert user.email == 'rosa.quispe@mail.com'


def test_lowercases_the_email_when_validated():
    user = UserFactory.build(email='Rosa.Quispe@Mail.COM')

    user.full_clean()

    assert user.email == 'rosa.quispe@mail.com'


def test_allows_several_users_without_email():
    User.objects.create_user(username='rosa')
    user = UserFactory.build(email='')

    user.full_clean()
    user.save()

    assert user.email is None


def test_rejects_a_duplicate_email():
    UserFactory(email='rosa@mail.com')
    user = UserFactory.build(email='ROSA@mail.com')

    with pytest.raises(ValidationError) as exc_info:
        user.full_clean()

    assert list(exc_info.value.message_dict) == ['email']


def test_the_database_rejects_an_email_in_uppercase():
    with pytest.raises(IntegrityError, match='accounts_user_email_lowercase'):
        UserFactory(email='Rosa@mail.com')
