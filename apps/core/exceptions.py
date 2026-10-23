from http import HTTPStatus
from typing import Any


class ApplicationError(Exception):
    status_code = HTTPStatus.BAD_REQUEST

    def __init__(self, message: str, detail: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail


class ServiceUnavailableError(ApplicationError):
    status_code = HTTPStatus.SERVICE_UNAVAILABLE
