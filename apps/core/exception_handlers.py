import logging
from http import HTTPStatus
from typing import Any

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404, HttpRequest, JsonResponse
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler, set_rollback

from apps.core.constants import (
    INTERNAL_SERVER_ERROR_MESSAGE,
    NOT_FOUND_MESSAGE,
    VALIDATION_ERROR_MESSAGE,
)
from apps.core.exceptions import ApplicationError

logger = logging.getLogger(__name__)


def error_envelope(message: str, detail: Any = None) -> dict[str, Any]:
    return {
        'success': False,
        'message': message,
        'data': None,
        'detail': detail,
    }


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response:
    if isinstance(exc, ApplicationError):
        set_rollback()
        return Response(
            error_envelope(message=exc.message, detail=exc.detail),
            status=exc.status_code,
        )
    exc = _to_drf_exception(exc)
    response = exception_handler(exc, context)

    if response is None:
        logger.exception('Unhandled exception', exc_info=exc)
        set_rollback()
        return Response(
            error_envelope(INTERNAL_SERVER_ERROR_MESSAGE),
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    response.data = _api_exception_envelope(exc)
    return response


def not_found_view(request: HttpRequest, exception: Exception) -> JsonResponse:
    return JsonResponse(
        error_envelope(NOT_FOUND_MESSAGE),
        status=HTTPStatus.NOT_FOUND,
        json_dumps_params={'ensure_ascii': False},
    )


def server_error_view(request: HttpRequest) -> JsonResponse:
    return JsonResponse(
        error_envelope(INTERNAL_SERVER_ERROR_MESSAGE),
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
        json_dumps_params={'ensure_ascii': False},
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
        return error_envelope(VALIDATION_ERROR_MESSAGE, {'fields': exc.detail})
    return error_envelope(str(exc.detail))
