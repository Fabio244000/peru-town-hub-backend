import logging
from http import HTTPStatus
from typing import Any, cast

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404, HttpRequest, JsonResponse
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler, set_rollback

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
from apps.core.exceptions import ApplicationError
from apps.core.middleware import current_request_id
from apps.core.throttles import RateLimited

logger = logging.getLogger(__name__)

# The security events every API logs (conventions/security.md §5).
SECURITY_EVENTS = (
    (exceptions.AuthenticationFailed, 'authentication_failed'),
    (exceptions.PermissionDenied, 'permission_denied'),
    (exceptions.Throttled, 'rate_limited'),
)


def error_envelope(
    message: str, code: str, extra: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        'success': False,
        'message': message,
        'data': None,
        'detail': {'code': code, **(extra or {})},
    }


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    if isinstance(exc, ApplicationError):
        set_rollback()
        return Response(
            error_envelope(exc.message, exc.code, exc.detail), status=exc.status_code
        )
    exc = _to_drf_exception(exc)
    response = exception_handler(exc, context)

    if response is None:
        logger.exception('Unhandled exception', exc_info=exc)
        set_rollback()
        return Response(
            _internal_error_envelope(), status=HTTPStatus.INTERNAL_SERVER_ERROR
        )

    # DRF only answers APIException (Http404 and PermissionDenied were converted).
    api_exception = cast(exceptions.APIException, exc)
    _log_security_event(api_exception, context)
    response.data = _api_exception_envelope(api_exception)
    return response


def not_found_view(request: HttpRequest, exception: Exception) -> JsonResponse:
    return JsonResponse(
        error_envelope(NOT_FOUND_MESSAGE, NOT_FOUND_CODE),
        status=HTTPStatus.NOT_FOUND,
        json_dumps_params={'ensure_ascii': False},
    )


def server_error_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        _internal_error_envelope(),
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
        json_dumps_params={'ensure_ascii': False},
    )


def _internal_error_envelope() -> dict[str, Any]:
    """With the request id, so support finds the error in the logs."""
    return error_envelope(
        INTERNAL_SERVER_ERROR_MESSAGE,
        INTERNAL_ERROR_CODE,
        {'request_id': current_request_id.get()},
    )


def _to_drf_exception(exc: Exception) -> Exception:
    if isinstance(exc, DjangoValidationError):
        return exceptions.ValidationError(as_serializer_error(exc))
    if isinstance(exc, Http404 | ObjectDoesNotExist):
        return exceptions.NotFound()
    if isinstance(exc, PermissionDenied):
        return exceptions.PermissionDenied()
    return exc


def _api_exception_envelope(exc: exceptions.APIException) -> dict[str, Any]:
    if isinstance(exc, exceptions.ValidationError):
        return error_envelope(
            VALIDATION_ERROR_MESSAGE, VALIDATION_ERROR_CODE, {'fields': exc.detail}
        )
    if isinstance(exc, exceptions.Throttled):
        message = exc.message if isinstance(exc, RateLimited) else RATE_LIMITED_MESSAGE
        return error_envelope(message, RATE_LIMITED_CODE)
    if isinstance(exc, exceptions.NotAuthenticated | exceptions.AuthenticationFailed):
        # One single text: never which credential failed.
        return error_envelope(UNAUTHENTICATED_MESSAGE, exc.default_code)
    return error_envelope(str(exc.detail), exc.default_code)


def _log_security_event(exc: exceptions.APIException, context: dict[str, Any]) -> None:
    event = next(
        (name for kind, name in SECURITY_EVENTS if isinstance(exc, kind)), None
    )
    if event is not None:
        logger.warning(
            'Security event: %s',
            event,
            extra={'event': event, 'user': _user_uuid(context)},
        )


def _user_uuid(context: dict[str, Any]) -> str | None:
    """The public uuid of the authenticated caller; never personal data."""
    user = getattr(context.get('request'), 'user', None)
    if user is None or not user.is_authenticated:
        return None
    return str(user.uuid)
