from http import HTTPStatus
from typing import Any


class ApplicationError(Exception):
    status_code = HTTPStatus.BAD_REQUEST

    def __init__(self, message: str, code: str, detail: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.detail = detail


class ConflictError(ApplicationError):
    status_code = HTTPStatus.CONFLICT


class ServiceUnavailableError(ApplicationError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
