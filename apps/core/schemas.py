from http import HTTPStatus
from typing import Any

from drf_spectacular.utils import OpenApiExample, inline_serializer
from rest_framework import serializers

from apps.core.constants import (
    INTERNAL_ERROR_CODE,
    INTERNAL_SERVER_ERROR_MESSAGE,
    VALIDATION_ERROR_CODE,
    VALIDATION_ERROR_MESSAGE,
)

EXAMPLE_REQUEST_ID = '3f2c9a1e-5b7d-4c21-9e8f-1a2b3c4d5e6f'


def success_envelope_schema(
    name: str, data: serializers.Field
) -> serializers.Serializer:
    return inline_serializer(
        name=name,
        fields={
            'success': serializers.BooleanField(),
            'message': serializers.CharField(allow_blank=True),
            'data': data,
            'detail': serializers.JSONField(allow_null=True),
        },
    )


def error_envelope_schema(
    name: str, detail: serializers.Field
) -> serializers.Serializer:
    return inline_serializer(
        name=name,
        fields={
            'success': serializers.BooleanField(),
            'message': serializers.CharField(),
            'data': serializers.JSONField(allow_null=True),
            'detail': detail,
        },
    )


# The shapes of `detail` (conventions/contracts.md §3).
ERROR_CODE_DETAIL = inline_serializer(
    name='ErrorCodeDetail', fields={'code': serializers.CharField()}
)
VALIDATION_ERROR_DETAIL = inline_serializer(
    name='ValidationErrorDetail',
    fields={
        'code': serializers.CharField(),
        'fields': serializers.DictField(
            child=serializers.ListField(child=serializers.CharField())
        ),
    },
)
INTERNAL_ERROR_DETAIL = inline_serializer(
    name='InternalErrorDetail',
    fields={'code': serializers.CharField(), 'request_id': serializers.CharField()},
)


def success_example(
    name: str, data: Any, status: int = HTTPStatus.OK, message: str = ''
) -> OpenApiExample:
    return OpenApiExample(
        name,
        value={'success': True, 'message': message, 'data': data, 'detail': None},
        response_only=True,
        status_codes=[str(status)],
    )


def error_example(
    name: str, status: int, message: str, detail: dict[str, Any]
) -> OpenApiExample:
    return OpenApiExample(
        name,
        value={'success': False, 'message': message, 'data': None, 'detail': detail},
        response_only=True,
        status_codes=[str(status)],
    )


def validation_example(name: str, fields: dict[str, list[str]]) -> OpenApiExample:
    return error_example(
        name,
        HTTPStatus.BAD_REQUEST,
        VALIDATION_ERROR_MESSAGE,
        {'code': VALIDATION_ERROR_CODE, 'fields': fields},
    )


INTERNAL_ERROR_EXAMPLE = error_example(
    'Unexpected error',
    HTTPStatus.INTERNAL_SERVER_ERROR,
    INTERNAL_SERVER_ERROR_MESSAGE,
    {'code': INTERNAL_ERROR_CODE, 'request_id': EXAMPLE_REQUEST_ID},
)
