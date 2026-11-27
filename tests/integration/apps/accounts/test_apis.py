from datetime import datetime
from http import HTTPStatus
from zoneinfo import ZoneInfo

import pytest
import time_machine
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.constants import (
    FIRST_NAMES_REQUIRED,
    POLICIES_NOT_ACCEPTED,
    SIGNUP_HOURLY_LIMIT_REACHED,
    SIGNUP_MONTHLY_LIMIT_REACHED,
    TOKEN_TYPE,
    USERNAME_LEADING_LETTERS_MISSING,
    USERNAME_TAKEN,
    USERNAME_TAKEN_CODE,
    PhoneStatus,
)
from apps.core.constants import (
    RATE_LIMITED_CODE,
    RATE_LIMITED_MESSAGE,
    VALIDATION_ERROR_CODE,
    VALIDATION_ERROR_MESSAGE,
)

pytestmark = pytest.mark.django_db

LIMA = ZoneInfo('America/Lima')
SIGN_UP = reverse('accounts:accounts-list')
USERNAME_AVAILABILITY = reverse('accounts:accounts-username-availability')
VALID_REQUEST = {
    'first_names': 'Rosa Elena',
    'last_names': 'Quispe Huamán',
    'username': 'rosaquispe2026',
    'password': 'Huanta#2026',
    'phone_country_code': '+51',
    'phone_number': '987654321',
    'policies_accepted': True,
}


def sign_up(client: APIClient, **overrides: object):
    return client.post(SIGN_UP, {**VALID_REQUEST, **overrides}, format='json')


def check_username(client: APIClient, username: str = 'rosaquispe2026'):
    return client.get(USERNAME_AVAILABILITY, {'username': username})


def error_envelope(message: str, detail: dict) -> dict:
    return {'success': False, 'message': message, 'data': None, 'detail': detail}


# POST accounts/


@time_machine.travel(datetime(2026, 11, 12, 15, 4, tzinfo=LIMA), tick=False)
def test_creates_the_account_and_signs_the_person_in():
    response = sign_up(APIClient())

    assert response.status_code == HTTPStatus.CREATED
    body = response.json()
    tokens = {key: body['data'].pop(key) for key in ('access_token', 'refresh_token')}
    assert body == {
        'success': True,
        'message': '',
        'data': {
            'username': 'rosaquispe2026',
            'first_names': 'rosa elena',
            'last_names': 'quispe huamán',
            'phone': '+51987654321',
            'phone_status': PhoneStatus.UNVERIFIED,
            'created_at': '2026-11-12T20:04:00Z',
            'token_type': TOKEN_TYPE,
            'expires_in': 15 * 60,
        },
        'detail': None,
    }
    assert all(tokens.values())


def test_answers_every_field_that_breaks_a_rule():
    response = sign_up(APIClient(), username='ro2saquispe')

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json() == error_envelope(
        VALIDATION_ERROR_MESSAGE,
        {
            'code': VALIDATION_ERROR_CODE,
            'fields': {'username': [USERNAME_LEADING_LETTERS_MISSING]},
        },
    )


@pytest.mark.parametrize(
    ('overrides', 'fields'),
    [
        ({'policies_accepted': False}, {'policies_accepted': [POLICIES_NOT_ACCEPTED]}),
        ({'first_names': None}, None),
    ],
)
def test_rejects_a_request_without_the_policies_or_with_a_wrong_type(overrides, fields):
    response = sign_up(APIClient(), **overrides)

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()['detail']['code'] == VALIDATION_ERROR_CODE
    if fields:
        assert response.json()['detail']['fields'] == fields


def test_asks_for_a_field_that_is_missing():
    request = {
        key: value for key, value in VALID_REQUEST.items() if key != 'first_names'
    }

    response = APIClient().post(SIGN_UP, request, format='json')

    assert response.json()['detail']['fields'] == {
        'first_names': [FIRST_NAMES_REQUIRED]
    }


def test_rejects_a_username_that_already_exists():
    client = APIClient()
    sign_up(client)

    response = sign_up(client, phone_number='987654322')

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json() == error_envelope(
        USERNAME_TAKEN, {'code': USERNAME_TAKEN_CODE}
    )


def test_a_public_api_ignores_an_invalid_token():
    client = APIClient(HTTP_AUTHORIZATION='Bearer not-a-token')

    assert sign_up(client).status_code == HTTPStatus.CREATED


# R8, L6: sign-up limits per device.


def test_limits_the_sign_up_requests_of_a_device_per_hour(settings):
    settings.SUPPORT_EMAIL = 'soporte@example.com'
    client = APIClient()
    with time_machine.travel(datetime(2026, 11, 12, 15, 0, tzinfo=LIMA), tick=False):
        for _ in range(10):
            sign_up(client, username='ro2saquispe')  # even a rejected one counts

        response = sign_up(client)

    assert response.status_code == HTTPStatus.TOO_MANY_REQUESTS
    assert response.json() == error_envelope(
        SIGNUP_HOURLY_LIMIT_REACHED.format(support_email='soporte@example.com'),
        {'code': RATE_LIMITED_CODE},
    )
    assert response['Retry-After'] == '3600'
    with time_machine.travel(datetime(2026, 11, 12, 16, 0, 1, tzinfo=LIMA), tick=False):
        assert sign_up(client).status_code == HTTPStatus.CREATED


def test_limits_the_sign_up_requests_of_a_device_per_calendar_month(settings):
    settings.SUPPORT_EMAIL = 'soporte@example.com'
    settings.SIGNUP_RATE_PER_MONTH = 2
    client = APIClient()
    with time_machine.travel(datetime(2026, 11, 30, 23, 0, tzinfo=LIMA), tick=False):
        sign_up(client, username='ro2saquispe')
        sign_up(client, username='ro2saquispe')

        response = sign_up(client)

    assert response.status_code == HTTPStatus.TOO_MANY_REQUESTS
    assert response.json() == error_envelope(
        SIGNUP_MONTHLY_LIMIT_REACHED.format(support_email='soporte@example.com'),
        {'code': RATE_LIMITED_CODE},
    )
    assert response['Retry-After'] == '3600'
    with time_machine.travel(datetime(2026, 12, 1, 0, 0, 1, tzinfo=LIMA), tick=False):
        assert sign_up(client).status_code == HTTPStatus.CREATED


def test_checking_usernames_does_not_count_for_the_sign_up_limit():
    client = APIClient()
    for _ in range(30):
        check_username(client)

    assert sign_up(client).status_code == HTTPStatus.CREATED


# GET accounts/username-availability/


@pytest.mark.parametrize('taken', [False, True])
def test_tells_whether_a_username_is_available(taken):
    client = APIClient()
    if taken:
        sign_up(client)

    response = check_username(client)

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'success': True,
        'message': '',
        'data': {'available': not taken},
        'detail': None,
    }


def test_rejects_checking_a_username_out_of_its_format():
    response = check_username(APIClient(), 'ro2saquispe')

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()['detail'] == {
        'code': VALIDATION_ERROR_CODE,
        'fields': {'username': [USERNAME_LEADING_LETTERS_MISSING]},
    }


def test_limits_the_username_checks_of_a_device(settings):
    settings.USERNAME_CHECK_RATE_PER_MINUTE = 2
    client = APIClient()
    check_username(client)
    check_username(client)

    response = check_username(client)

    assert response.status_code == HTTPStatus.TOO_MANY_REQUESTS
    assert response.json() == error_envelope(
        RATE_LIMITED_MESSAGE, {'code': RATE_LIMITED_CODE}
    )
    assert response['Retry-After']


# Every API: the base limit.


def test_an_api_without_its_own_limit_gets_the_base_one(settings):
    settings.API_ANON_RATE_PER_MINUTE = 1
    client = APIClient()
    client.get(reverse('health'))

    response = client.get(reverse('health'))

    assert response.status_code == HTTPStatus.TOO_MANY_REQUESTS
    assert response.json()['message'] == RATE_LIMITED_MESSAGE
