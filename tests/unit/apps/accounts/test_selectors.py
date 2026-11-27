import pytest
from django.core.exceptions import ValidationError

from apps.accounts.constants import USERNAME_LEADING_LETTERS_MISSING, USERNAME_REQUIRED
from apps.accounts.selectors import username_is_available
from tests.factories.accounts import UserFactory

pytestmark = pytest.mark.django_db


def test_a_username_nobody_has_is_available():
    assert username_is_available(username=' rosaquispe2026 ') is True


def test_a_username_already_taken_is_not_available():
    UserFactory(username='rosaquispe2026')

    assert username_is_available(username='rosaquispe2026') is False


def test_asks_for_a_missing_username():
    with pytest.raises(ValidationError) as exc_info:
        username_is_available(username='  ')

    assert exc_info.value.message_dict == {'username': [USERNAME_REQUIRED]}


def test_a_username_out_of_its_format_is_rejected_before_looking_for_it():
    with pytest.raises(ValidationError) as exc_info:
        username_is_available(username='ro2saquispe')

    assert exc_info.value.message_dict == {
        'username': [USERNAME_LEADING_LETTERS_MISSING]
    }
