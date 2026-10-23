from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import serializers

from apps.core.schemas import error_envelope_schema, success_envelope_schema
from apps.health.constants import (
    DATABASE_DEPENDENCY,
    DATABASE_INTEGRATION_ERROR,
    DEPENDENCY_ERROR,
    DEPENDENCY_OK,
    HEALTH_OK_MESSAGE,
)

health_check_schema = extend_schema(
    summary='Check the system and its dependencies',
    responses={
        200: success_envelope_schema(
            'HealthCheckOk',
            data=serializers.DictField(child=serializers.CharField()),
        ),
        503: error_envelope_schema(
            'HealthCheckUnavailable',
            detail=serializers.DictField(child=serializers.CharField()),
        ),
    },
    examples=[
        OpenApiExample(
            'System healthy',
            value={
                'success': True,
                'message': HEALTH_OK_MESSAGE,
                'data': {DATABASE_DEPENDENCY: DEPENDENCY_OK},
                'detail': None,
            },
            response_only=True,
            status_codes=['200'],
        ),
        OpenApiExample(
            'Database unavailable',
            value={
                'success': False,
                'message': DATABASE_INTEGRATION_ERROR,
                'data': None,
                'detail': {DATABASE_DEPENDENCY: DEPENDENCY_ERROR},
            },
            response_only=True,
            status_codes=['503'],
        ),
    ],
)
