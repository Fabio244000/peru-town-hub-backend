from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import time_machine
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from apps.accounts.constants import (
    FIRST_NAMES_REQUIRED,
    LAST_NAMES_REQUIRED,
    NAME_INVALID_CHARACTERS,
    NAME_TOO_LONG,
    NAME_TOO_SHORT,
    PASSWORD_LENGTH_INVALID,
    PASSWORD_MISSING_DIGIT,
    PASSWORD_MISSING_SPECIAL,
    PASSWORD_REPEATED_CHARACTER,
    PASSWORD_REQUIRED,
    PASSWORD_SIMILAR,
    PASSWORD_WITH_SPACES,
    PHONE_COUNTRY_INVALID,
    PHONE_DIGITS_ONLY,
    PHONE_INVALID,
    PHONE_INVALID_PREFIX,
    PHONE_REQUIRED,
    PHONE_TAKEN,
    PHONE_TAKEN_CODE,
    USERNAME_HAS_ACCENTS,
    USERNAME_HAS_SPACES,
    USERNAME_INVALID_CHARACTERS,
    USERNAME_LEADING_LETTERS_MISSING,
    USERNAME_REQUIRED,
    USERNAME_TAKEN,
    USERNAME_TAKEN_CODE,
    USERNAME_TOO_LONG,
    USERNAME_TOO_SHORT,
    PhoneStatus,
)
from apps.accounts.dtos import NewAccount, RegisteredAccount
from apps.accounts.services import AccountRegistrationService
from apps.core.constants import JWT_AUDIENCE, JWT_ISSUER
from apps.core.exceptions import ConflictError

pytestmark = pytest.mark.django_db

VALID_ACCOUNT = {
    'first_names': 'Rosa Elena',
    'last_names': 'Quispe Huamán',
    'username': 'rosaquispe2026',
    'password': 'Huanta#2026',
    'phone_country_code': '+51',
    'phone_number': '987654321',
}
# Filler without a character repeated in a row (R3).
FILLER = 'abcdefghij' * 5
PERU_NUMBERING = PHONE_INVALID.format(
    country='Perú', digits=9, prefix=PHONE_INVALID_PREFIX.format(digit=9)
)


def register(**overrides: Any) -> RegisteredAccount:
    account = NewAccount(**{**VALID_ACCOUNT, **overrides})
    return AccountRegistrationService().register(account=account)


def field_errors(**overrides: Any) -> dict[str, list[str]]:
    with pytest.raises(ValidationError) as exc_info:
        register(**overrides)
    return exc_info.value.message_dict


# R1, L1: names.


def test_stores_the_names_in_lowercase_with_one_space_between_words(stored_account):
    register(first_names='  María-José ', last_names="Q'ispe   Huamán")

    stored = stored_account('rosaquispe2026')
    assert (stored['first_name'], stored['last_name']) == (
        'maría-josé',
        "q'ispe huamán",
    )


@pytest.mark.parametrize('name', ['Li', 'a' * 250])
def test_accepts_a_name_at_its_length_limits(name, stored_account):
    register(last_names=name)

    assert stored_account('rosaquispe2026')['last_name'] == name.lower()


@pytest.mark.parametrize(
    ('name', 'message'),
    [
        ('Rosa2', NAME_INVALID_CHARACTERS),
        ('A', NAME_TOO_SHORT),
        ('a' * 251, NAME_TOO_LONG),
    ],
)
@pytest.mark.parametrize('field', ['first_names', 'last_names'])
def test_rejects_a_name_out_of_its_format(field, name, message):
    assert field_errors(**{field: name}) == {field: [message]}


@pytest.mark.parametrize(
    ('field', 'message'),
    [('first_names', FIRST_NAMES_REQUIRED), ('last_names', LAST_NAMES_REQUIRED)],
)
def test_asks_for_a_missing_name(field, message):
    assert field_errors(**{field: '   '}) == {field: [message]}


# R2, L2: username.


def test_creates_the_account_with_its_username():
    registered = register(username=' rosaquispe2026 ')

    assert registered.username == 'rosaquispe2026'


@pytest.mark.parametrize('username', ['rosaquis', 'rosaquispe' + '1' * 20])
def test_accepts_a_username_at_its_length_limits(username):
    assert register(username=username).username == username


@pytest.mark.parametrize(
    ('username', 'messages'),
    [
        ('ro2saquispe', [USERNAME_LEADING_LETTERS_MISSING]),
        ('peñaloza12', [USERNAME_HAS_ACCENTS]),
        ('rosa quispe', [USERNAME_HAS_SPACES]),
        ('RosaQuispe1', [USERNAME_INVALID_CHARACTERS]),
        ('rosaq', [USERNAME_TOO_SHORT.format(missing=3)]),
        ('rosaquispe' + '1' * 21, [USERNAME_TOO_LONG]),
        (
            'ro2 ñ',
            [
                USERNAME_HAS_SPACES,
                USERNAME_HAS_ACCENTS,
                USERNAME_LEADING_LETTERS_MISSING,
                USERNAME_TOO_SHORT.format(missing=3),
            ],
        ),
    ],
)
def test_rejects_a_username_with_every_condition_it_breaks(username, messages):
    assert field_errors(username=username) == {'username': messages}


def test_asks_for_a_missing_username():
    assert field_errors(username='') == {'username': [USERNAME_REQUIRED]}


def test_rejects_a_username_that_already_exists():
    register()

    with pytest.raises(ConflictError) as exc_info:
        register(phone_number='987654322')

    assert (exc_info.value.message, exc_info.value.code) == (
        USERNAME_TAKEN,
        USERNAME_TAKEN_CODE,
    )


# R3, R4, L3, L5: password.


@pytest.mark.parametrize('password', ['Huanta#2026', '1234@adas_1231', 'Huaaanta#1'])
def test_accepts_a_password_that_meets_every_condition(password, stored_account):
    register(password=password)

    assert check_password(password, stored_account('rosaquispe2026')['password'])


def test_never_stores_the_password_in_plain_text(stored_account):
    register()

    assert stored_account('rosaquispe2026')['password'] != VALID_ACCOUNT['password']


@pytest.mark.parametrize(
    ('password', 'messages'),
    [
        ('huanta2026', [PASSWORD_MISSING_SPECIAL]),
        ('Huanta #2026', [PASSWORD_WITH_SPACES]),
        ('11111111#a', [PASSWORD_REPEATED_CHARACTER]),
        ('Huanta#abc', [PASSWORD_MISSING_DIGIT]),
        ('Ab#1', [PASSWORD_LENGTH_INVALID]),
        ('Ab#1' + FILLER[:47], [PASSWORD_LENGTH_INVALID]),
        (
            'aaaa a',
            [
                PASSWORD_LENGTH_INVALID,
                PASSWORD_MISSING_DIGIT,
                PASSWORD_MISSING_SPECIAL,
                PASSWORD_WITH_SPACES,
                PASSWORD_REPEATED_CHARACTER,
            ],
        ),
    ],
)
def test_rejects_a_password_with_every_condition_it_misses(password, messages):
    assert field_errors(password=password) == {'password': messages}


def test_accepts_a_password_of_fifty_characters():
    assert register(password='Ab#1' + FILLER[:46]).username == 'rosaquispe2026'


def test_asks_for_a_missing_password():
    assert field_errors(password='') == {'password': [PASSWORD_REQUIRED]}


@pytest.mark.parametrize(
    'password',
    [
        'rosaquispe20#',  # 3 characters from the username
        'Rosaquispe#123',  # 4 from the username, without minding case
        'Elena#26',  # 3 from a first name
        'Huamán#1',  # 2 from a last name
    ],
)
def test_rejects_a_password_close_to_the_username_or_a_name(password):
    assert field_errors(username='rosaquispe', password=password) == {
        'password': [PASSWORD_SIMILAR]
    }


def test_accepts_a_password_five_characters_away_from_the_username():
    registered = register(username='rosaquispe', password='rosaquispe#1234')

    assert registered.username == 'rosaquispe'


# R5, L4: cellphone.


def test_stores_the_cellphone_in_e164_waiting_for_verification():
    registered = register(phone_country_code='+51', phone_number='987654321')

    assert (registered.phone, registered.phone_status) == (
        '+51987654321',
        PhoneStatus.UNVERIFIED,
    )


@pytest.mark.parametrize('number', ['98765432', '887654321', '1'])
def test_rejects_a_cellphone_out_of_its_country_numbering(number):
    assert field_errors(phone_number=number) == {'phone_number': [PERU_NUMBERING]}


def test_describes_a_numbering_without_a_single_leading_digit():
    chile = PHONE_INVALID.format(country='Chile', digits=9, prefix='')

    assert field_errors(phone_country_code='+56', phone_number='12345') == {
        'phone_number': [chile]
    }


@pytest.mark.parametrize(
    ('country_code', 'number', 'message'),
    [
        ('+51', '98765-4321', PHONE_DIGITS_ONLY),
        ('+51', '', PHONE_REQUIRED),
        ('+999', '987654321', PHONE_COUNTRY_INVALID),
        ('+0', '987654321', PHONE_COUNTRY_INVALID),
    ],
)
def test_rejects_a_cellphone_that_cannot_be_read(country_code, number, message):
    errors = field_errors(phone_country_code=country_code, phone_number=number)

    assert errors == {'phone_number': [message]}


def test_rejects_a_cellphone_that_already_has_an_account():
    register()

    with pytest.raises(ConflictError) as exc_info:
        register(username='rosaquispe2027')

    assert (exc_info.value.message, exc_info.value.code) == (
        PHONE_TAKEN,
        PHONE_TAKEN_CODE,
    )


# Every field at once.


def test_reports_every_invalid_field_at_once():
    errors = field_errors(first_names='Rosa2', username='ro2saquispe', password='')

    assert set(errors) == {'first_names', 'username', 'password'}


# R6, R9: acceptance of the policies.


@time_machine.travel(datetime(2026, 11, 12, 20, 4, tzinfo=UTC), tick=False)
def test_records_the_moment_the_person_accepted_the_policies(stored_account):
    register()

    stored = stored_account('rosaquispe2026')
    moment = datetime(2026, 11, 12, 20, 4, tzinfo=UTC)
    assert (stored['policies_accepted_at'], stored['date_joined']) == (moment, moment)


# R7: the session.


def test_signs_the_person_in_with_tokens_that_name_its_public_uuid(stored_account):
    registered = register()

    access = AccessToken(registered.tokens.access)
    refresh = RefreshToken(registered.tokens.refresh)
    assert access['user_id'] == str(stored_account('rosaquispe2026')['uuid'])
    assert (access['iss'], access['aud']) == (JWT_ISSUER, JWT_AUDIENCE)
    assert access['exp'] - access['iat'] == registered.tokens.expires_in == 15 * 60
    assert refresh['exp'] - refresh['iat'] == timedelta(days=7).total_seconds()


# N1: retrying does not duplicate.


def test_a_retry_is_rejected_as_a_taken_username_and_keeps_one_account(
    count_accounts,
):
    register()

    with pytest.raises(ConflictError) as exc_info:
        register()

    assert exc_info.value.code == USERNAME_TAKEN_CODE
    assert count_accounts() == 1
