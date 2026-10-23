from http import HTTPStatus

from apps.core.exceptions import ApplicationError, ServiceUnavailableError

ERROR_MESSAGE = 'Algo salió mal'


def test_application_error_keeps_message_and_detail():
    error = ApplicationError(ERROR_MESSAGE, detail={'field': 'value'})

    assert error.message == ERROR_MESSAGE
    assert error.detail == {'field': 'value'}
    assert str(error) == ERROR_MESSAGE


def test_application_error_defaults_to_bad_request_without_detail():
    error = ApplicationError(ERROR_MESSAGE)

    assert error.detail is None
    assert error.status_code == HTTPStatus.BAD_REQUEST


def test_service_unavailable_error_is_an_application_error_with_503():
    error = ServiceUnavailableError(ERROR_MESSAGE)

    assert isinstance(error, ApplicationError)
    assert error.status_code == HTTPStatus.SERVICE_UNAVAILABLE
