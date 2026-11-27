from http import HTTPStatus

from apps.core.exceptions import (
    ApplicationError,
    ConflictError,
    ServiceUnavailableError,
)

ERROR_MESSAGE = 'Algo salió mal'
ERROR_CODE = 'something_wrong'


def test_application_error_keeps_message_code_and_detail():
    error = ApplicationError(ERROR_MESSAGE, ERROR_CODE, detail={'field': 'value'})

    assert (error.message, error.code, error.detail) == (
        ERROR_MESSAGE,
        ERROR_CODE,
        {'field': 'value'},
    )
    assert str(error) == ERROR_MESSAGE


def test_application_error_defaults_to_bad_request_without_detail():
    error = ApplicationError(ERROR_MESSAGE, ERROR_CODE)

    assert error.detail is None
    assert error.status_code == HTTPStatus.BAD_REQUEST


def test_service_unavailable_error_is_an_application_error_with_503():
    error = ServiceUnavailableError(ERROR_MESSAGE, ERROR_CODE)

    assert isinstance(error, ApplicationError)
    assert error.status_code == HTTPStatus.SERVICE_UNAVAILABLE


def test_conflict_error_is_an_application_error_with_409():
    error = ConflictError(ERROR_MESSAGE, ERROR_CODE)

    assert isinstance(error, ApplicationError)
    assert error.status_code == HTTPStatus.CONFLICT
