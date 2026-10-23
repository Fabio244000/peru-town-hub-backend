import json
import logging
from http import HTTPStatus

import pytest
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions

from apps.core.constants import (
    INTERNAL_SERVER_ERROR_MESSAGE,
    VALIDATION_ERROR_MESSAGE,
)
from apps.core.exception_handlers import custom_exception_handler, server_error_view
from apps.core.exceptions import ApplicationError, ServiceUnavailableError

ERROR_MESSAGE = 'Algo salió mal'


def handle(exc):
    return custom_exception_handler(exc, context={})


def assert_error_envelope(response, status, message, detail=None):
    assert response.status_code == status
    assert response.data == {
        'success': False,
        'message': message,
        'data': None,
        'detail': detail,
    }


def test_application_error_uses_its_message_and_detail():
    response = handle(ApplicationError(ERROR_MESSAGE, detail={'type': 'RULE'}))

    assert_error_envelope(
        response, HTTPStatus.BAD_REQUEST, ERROR_MESSAGE, {'type': 'RULE'}
    )


def test_application_error_subclass_uses_its_own_status():
    response = handle(ServiceUnavailableError(ERROR_MESSAGE))

    assert_error_envelope(response, HTTPStatus.SERVICE_UNAVAILABLE, ERROR_MESSAGE)


def test_drf_validation_error_puts_errors_under_fields():
    errors = {'name': ['Este campo es requerido.']}

    response = handle(exceptions.ValidationError(errors))

    assert_error_envelope(
        response, HTTPStatus.BAD_REQUEST, VALIDATION_ERROR_MESSAGE, {'fields': errors}
    )


def test_django_validation_error_is_translated_to_non_field_errors():
    response = handle(DjangoValidationError(ERROR_MESSAGE))

    assert_error_envelope(
        response,
        HTTPStatus.BAD_REQUEST,
        VALIDATION_ERROR_MESSAGE,
        {'fields': {'non_field_errors': [ERROR_MESSAGE]}},
    )


@pytest.mark.parametrize(
    ('exc', 'status', 'drf_exception'),
    [
        (Http404(), HTTPStatus.NOT_FOUND, exceptions.NotFound()),
        (ObjectDoesNotExist(), HTTPStatus.NOT_FOUND, exceptions.NotFound()),
        (PermissionDenied(), HTTPStatus.FORBIDDEN, exceptions.PermissionDenied()),
        (
            exceptions.NotAuthenticated(),
            HTTPStatus.UNAUTHORIZED,
            exceptions.NotAuthenticated(),
        ),
        (
            exceptions.MethodNotAllowed('DELETE'),
            HTTPStatus.METHOD_NOT_ALLOWED,
            exceptions.MethodNotAllowed('DELETE'),
        ),
    ],
)
def test_framework_errors_use_drf_message(exc, status, drf_exception):
    response = handle(exc)

    assert_error_envelope(response, status, str(drf_exception.detail))


def test_throttled_keeps_retry_after_header():
    response = handle(exceptions.Throttled(wait=30))

    assert response.status_code == HTTPStatus.TOO_MANY_REQUESTS
    assert response['Retry-After'] == '30'


def test_unexpected_error_returns_generic_500_and_logs_it(caplog):
    with caplog.at_level(logging.ERROR):
        response = handle(RuntimeError('database password is secret'))

    assert_error_envelope(
        response, HTTPStatus.INTERNAL_SERVER_ERROR, INTERNAL_SERVER_ERROR_MESSAGE
    )
    assert 'database password is secret' in caplog.text


def test_server_error_view_returns_generic_500_envelope(rf):
    response = server_error_view(rf.get('/'))

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert json.loads(response.content) == {
        'success': False,
        'message': INTERNAL_SERVER_ERROR_MESSAGE,
        'data': None,
        'detail': None,
    }
