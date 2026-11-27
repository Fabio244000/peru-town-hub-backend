from http import HTTPStatus

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema

from apps.accounts.constants import (
    NAME_INVALID_CHARACTERS,
    PASSWORD_MISSING_SPECIAL,
    PASSWORD_SIMILAR,
    PHONE_INVALID,
    PHONE_INVALID_PREFIX,
    PHONE_TAKEN,
    PHONE_TAKEN_CODE,
    POLICIES_NOT_ACCEPTED,
    SIGNUP_HOURLY_LIMIT_REACHED,
    SIGNUP_MONTHLY_LIMIT_REACHED,
    TOKEN_TYPE,
    USERNAME_LEADING_LETTERS_MISSING,
    USERNAME_LENGTH,
    USERNAME_PATTERN,
    USERNAME_REQUIRED,
    USERNAME_TAKEN,
    USERNAME_TAKEN_CODE,
    PhoneStatus,
)
from apps.accounts.serializers import (
    AccountCreateInputSerializer,
    AccountCreateOutputSerializer,
    UsernameAvailabilityOutputSerializer,
)
from apps.core.constants import RATE_LIMITED_CODE, RATE_LIMITED_MESSAGE
from apps.core.schemas import (
    ERROR_CODE_DETAIL,
    INTERNAL_ERROR_DETAIL,
    INTERNAL_ERROR_EXAMPLE,
    VALIDATION_ERROR_DETAIL,
    error_envelope_schema,
    error_example,
    success_envelope_schema,
    success_example,
    validation_example,
)

# Never the real support address: this repository is public.
EXAMPLE_SUPPORT_EMAIL = 'soporte@example.com'
PERU_NUMBERING = PHONE_INVALID.format(
    country='Perú', digits=9, prefix=PHONE_INVALID_PREFIX.format(digit=9)
)

account_create_schema = extend_schema(
    summary='Create an account',
    description=(
        'Creates the account of a person (names, username, password and cellphone, '
        'waiting for verification) and signs them in with JWT tokens. Public. '
        'Limited per device: per hour and per calendar month (Peru time).'
    ),
    request=AccountCreateInputSerializer,
    responses={
        201: success_envelope_schema(
            'AccountCreated', data=AccountCreateOutputSerializer()
        ),
        400: error_envelope_schema(
            'AccountCreateInvalid', detail=VALIDATION_ERROR_DETAIL
        ),
        409: error_envelope_schema('AccountCreateConflict', detail=ERROR_CODE_DETAIL),
        429: error_envelope_schema(
            'AccountCreateRateLimited', detail=ERROR_CODE_DETAIL
        ),
        500: error_envelope_schema('AccountCreateFailed', detail=INTERNAL_ERROR_DETAIL),
    },
    examples=[
        OpenApiExample(
            'Valid request',
            value={
                'first_names': 'Rosa Elena',
                'last_names': 'Quispe Huamán',
                'username': 'rosaquispe2026',
                'password': 'Huanta#2026',
                'phone_country_code': '+51',
                'phone_number': '987654321',
                'policies_accepted': True,
            },
            request_only=True,
        ),
        success_example(
            'Account created',
            {
                'username': 'rosaquispe2026',
                'first_names': 'rosa elena',
                'last_names': 'quispe huamán',
                'phone': '+51987654321',
                'phone_status': PhoneStatus.UNVERIFIED.value,
                'created_at': '2026-11-12T20:04:00Z',
                'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.access',
                'refresh_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh',
                'token_type': TOKEN_TYPE,
                'expires_in': 900,
            },
            status=HTTPStatus.CREATED,
        ),
        validation_example('Invalid name', {'first_names': [NAME_INVALID_CHARACTERS]}),
        validation_example(
            'Invalid username', {'username': [USERNAME_LEADING_LETTERS_MISSING]}
        ),
        validation_example('Weak password', {'password': [PASSWORD_MISSING_SPECIAL]}),
        validation_example('Password like a name', {'password': [PASSWORD_SIMILAR]}),
        validation_example('Invalid cellphone', {'phone_number': [PERU_NUMBERING]}),
        validation_example(
            'Policies not accepted', {'policies_accepted': [POLICIES_NOT_ACCEPTED]}
        ),
        error_example(
            'Username taken',
            HTTPStatus.CONFLICT,
            USERNAME_TAKEN,
            {'code': USERNAME_TAKEN_CODE},
        ),
        error_example(
            'Cellphone taken',
            HTTPStatus.CONFLICT,
            PHONE_TAKEN,
            {'code': PHONE_TAKEN_CODE},
        ),
        error_example(
            'Hourly limit of the device',
            HTTPStatus.TOO_MANY_REQUESTS,
            SIGNUP_HOURLY_LIMIT_REACHED.format(support_email=EXAMPLE_SUPPORT_EMAIL),
            {'code': RATE_LIMITED_CODE},
        ),
        error_example(
            'Monthly limit of the device',
            HTTPStatus.TOO_MANY_REQUESTS,
            SIGNUP_MONTHLY_LIMIT_REACHED.format(support_email=EXAMPLE_SUPPORT_EMAIL),
            {'code': RATE_LIMITED_CODE},
        ),
        INTERNAL_ERROR_EXAMPLE,
    ],
)

username_availability_schema = extend_schema(
    summary='Check whether a username is available',
    description=(
        'Tells whether a username can still be taken, while the person writes it. '
        'Public; limited per device per minute. It does not count for the sign-up '
        'limit.'
    ),
    parameters=[
        OpenApiParameter(
            'username',
            {
                'type': 'string',
                'minLength': USERNAME_LENGTH[0],
                'maxLength': USERNAME_LENGTH[1],
                'pattern': USERNAME_PATTERN,
            },
            required=True,
            description=(
                'The username to check: lowercase letters without ñ or accents and '
                'digits; the first 3 are letters.'
            ),
        )
    ],
    responses={
        200: success_envelope_schema(
            'UsernameAvailability', data=UsernameAvailabilityOutputSerializer()
        ),
        400: error_envelope_schema(
            'UsernameAvailabilityInvalid', detail=VALIDATION_ERROR_DETAIL
        ),
        429: error_envelope_schema(
            'UsernameAvailabilityRateLimited', detail=ERROR_CODE_DETAIL
        ),
        500: error_envelope_schema(
            'UsernameAvailabilityFailed', detail=INTERNAL_ERROR_DETAIL
        ),
    },
    examples=[
        success_example('Available', {'available': True}),
        success_example('Taken', {'available': False}),
        validation_example('Missing username', {'username': [USERNAME_REQUIRED]}),
        validation_example(
            'Invalid username', {'username': [USERNAME_LEADING_LETTERS_MISSING]}
        ),
        error_example(
            'Too many checks',
            HTTPStatus.TOO_MANY_REQUESTS,
            RATE_LIMITED_MESSAGE,
            {'code': RATE_LIMITED_CODE},
        ),
        INTERNAL_ERROR_EXAMPLE,
    ],
)
