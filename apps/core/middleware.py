import logging
import re
import time
from collections.abc import Callable
from contextvars import ContextVar
from uuid import uuid4

from django.http import HttpRequest
from django.http.response import HttpResponseBase

REQUEST_ID_HEADER = 'X-Request-ID'
# What a client may send as its own id: nothing that could forge a log line.
SAFE_REQUEST_ID = r'[A-Za-z0-9-]{1,64}'

current_request_id: ContextVar[str] = ContextVar('request_id', default='')
request_logger = logging.getLogger('apps.core.requests')


class RequestIdMiddleware:
    """Gives every request an id, sends it back and logs the request's line."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponseBase]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        request_id = self._request_id(request)
        token = current_request_id.set(request_id)
        started = time.perf_counter()
        try:
            response = self.get_response(request)
            response[REQUEST_ID_HEADER] = request_id
            self._log(request, response, started)
            return response
        finally:
            current_request_id.reset(token)

    def _request_id(self, request: HttpRequest) -> str:
        sent = request.headers.get(REQUEST_ID_HEADER, '')
        return sent if re.fullmatch(SAFE_REQUEST_ID, sent) else str(uuid4())

    def _log(
        self, request: HttpRequest, response: HttpResponseBase, started: float
    ) -> None:
        # The path only: a query string can carry personal data.
        request_logger.info(
            'request',
            extra={
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'duration_ms': round((time.perf_counter() - started) * 1000),
                'request_id': current_request_id.get(),
            },
        )
