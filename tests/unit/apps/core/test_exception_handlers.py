import json
import logging
from http import HTTPStatus

import pytest
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions

from apps.core.constants import (
    INTERNAL_ERROR_CODE,
    INTERNAL_SERVER_ERROR_MESSAGE,
    NOT_FOUND_CODE,
    NOT_FOUND_MESSAGE,
    RATE_LIMITED_CODE,
    RATE_LIMITED_MESSAGE,
    UNAUTHENTICATED_MESSAGE,
    VALIDATION_ERROR_CODE,
    VALIDATION_ERROR_MESSAGE,
)
from apps.core.exception_handlers import (
    custom_exception_handler,
    not_found_view,
    server_error_view,
)
from apps.core.exceptions import ApplicationError, ServiceUnavailableError
from apps.core.middleware import current_request_id
from apps.core.throttles import RateLimited

ERROR_MESSAGE = 'Algo salió mal'
ERROR_CODE = 'something_wrong'
REQUEST_ID = 'a1b2c3'


@pytest.fixture
def request_id():
    token = current_request_id.set(REQUEST_ID)
    yield REQUEST_ID
    current_request_id.reset(token)


def handle(exc):
    return custom_exception_handler(exc, context={})


def assert_error_envelope(response, status, message, detail):
    assert response.status_code == status
    assert response.data == {
        'success': False,
        'message': message,
        'data': None,
        'detail': detail,
    }


def test_application_error_uses_its_message_code_and_detail():
    response = handle(
        ApplicationError(ERROR_MESSAGE, ERROR_CODE, detail={'type': 'RULE'})
    )

    assert_error_envelope(
        response,
        HTTPStatus.BAD_REQUEST,
        ERROR_MESSAGE,
        {'code': ERROR_CODE, 'type': 'RULE'},
    )


def test_application_error_subclass_uses_its_own_status():
    response = handle(ServiceUnavailableError(ERROR_MESSAGE, ERROR_CODE))

    assert_error_envelope(
        response, HTTPStatus.SERVICE_UNAVAILABLE, ERROR_MESSAGE, {'code': ERROR_CODE}
    )


def test_drf_validation_error_puts_errors_under_fields():
    errors = {'name': ['Este campo es requerido.']}

    response = handle(exceptions.ValidationError(errors))

    assert_error_envelope(
        response,
        HTTPStatus.BAD_REQUEST,
        VALIDATION_ERROR_MESSAGE,
        {'code': VALIDATION_ERROR_CODE, 'fields': errors},
    )


def test_django_validation_error_keeps_its_fields():
    response = handle(DjangoValidationError({'username': [ERROR_MESSAGE]}))

    assert_error_envelope(
        response,
        HTTPStatus.BAD_REQUEST,
        VALIDATION_ERROR_MESSAGE,
        {'code': VALIDATION_ERROR_CODE, 'fields': {'username': [ERROR_MESSAGE]}},
    )


def test_django_validation_error_without_field_goes_to_non_field_errors():
    response = handle(DjangoValidationError(ERROR_MESSAGE))

    assert_error_envelope(
        response,
        HTTPStatus.BAD_REQUEST,
        VALIDATION_ERROR_MESSAGE,
        {
            'code': VALIDATION_ERROR_CODE,
            'fields': {'non_field_errors': [ERROR_MESSAGE]},
        },
    )


@pytest.mark.parametrize(
    ('exc', 'status', 'drf_exception'),
    [
        (Http404(), HTTPStatus.NOT_FOUND, exceptions.NotFound()),
        (ObjectDoesNotExist(), HTTPStatus.NOT_FOUND, exceptions.NotFound()),
        (PermissionDenied(), HTTPStatus.FORBIDDEN, exceptions.PermissionDenied()),
        (
            exceptions.MethodNotAllowed('DELETE'),
            HTTPStatus.METHOD_NOT_ALLOWED,
            exceptions.MethodNotAllowed('DELETE'),
        ),
    ],
)
def test_framework_errors_use_drf_message_and_code(exc, status, drf_exception):
    response = handle(exc)

    assert_error_envelope(
        response,
        status,
        str(drf_exception.detail),
        {'code': drf_exception.default_code},
    )


@pytest.mark.parametrize(
    'exc',
    [
        exceptions.NotAuthenticated(),
        exceptions.AuthenticationFailed({'detail': 'Token is invalid', 'code': 'x'}),
    ],
)
def test_every_credential_failure_answers_one_single_message(exc):
    response = handle(exc)

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.data['message'] == UNAUTHENTICATED_MESSAGE


def test_a_limit_without_its_own_message_answers_the_generic_one():
    response = handle(exceptions.Throttled(wait=30))

    assert_error_envelope(
        response,
        HTTPStatus.TOO_MANY_REQUESTS,
        RATE_LIMITED_MESSAGE,
        {'code': RATE_LIMITED_CODE},
    )
    assert response['Retry-After'] == '30'


def test_a_limit_with_its_own_message_answers_it():
    response = handle(RateLimited(ERROR_MESSAGE, wait=3600))

    assert_error_envelope(
        response,
        HTTPStatus.TOO_MANY_REQUESTS,
        ERROR_MESSAGE,
        {'code': RATE_LIMITED_CODE},
    )
    assert response['Retry-After'] == '3600'


@pytest.mark.parametrize(
    ('exc', 'event'),
    [
        (exceptions.AuthenticationFailed(), 'authentication_failed'),
        (exceptions.PermissionDenied(), 'permission_denied'),
        (exceptions.Throttled(wait=30), 'rate_limited'),
    ],
)
def test_logs_a_security_event_as_a_warning(exc, event, caplog):
    with caplog.at_level(logging.WARNING):
        handle(exc)

    [record] = [r for r in caplog.records if getattr(r, 'event', None) == event]
    assert record.levelno == logging.WARNING


def test_unexpected_error_returns_generic_500_with_its_request_id(request_id, caplog):
    with caplog.at_level(logging.ERROR):
        response = handle(RuntimeError('database password is secret'))

    assert_error_envelope(
        response,
        HTTPStatus.INTERNAL_SERVER_ERROR,
        INTERNAL_SERVER_ERROR_MESSAGE,
        {'code': INTERNAL_ERROR_CODE, 'request_id': request_id},
    )
    assert 'database password is secret' in caplog.text


def test_server_error_view_returns_generic_500_with_its_request_id(rf, request_id):
    response = server_error_view(rf.get('/'))

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert json.loads(response.content) == {
        'success': False,
        'message': INTERNAL_SERVER_ERROR_MESSAGE,
        'data': None,
        'detail': {'code': INTERNAL_ERROR_CODE, 'request_id': request_id},
    }


def test_not_found_view_returns_the_not_found_envelope(rf):
    response = not_found_view(rf.get('/missing/'), Http404())

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert json.loads(response.content) == {
        'success': False,
        'message': NOT_FOUND_MESSAGE,
        'data': None,
        'detail': {'code': NOT_FOUND_CODE},
    }
