from http import HTTPStatus

from drf_spectacular.utils import extend_schema
from rest_framework import serializers

from apps.core.constants import RATE_LIMITED_CODE, RATE_LIMITED_MESSAGE
from apps.core.schemas import (
    ERROR_CODE_DETAIL,
    INTERNAL_ERROR_DETAIL,
    INTERNAL_ERROR_EXAMPLE,
    error_envelope_schema,
    error_example,
    success_envelope_schema,
    success_example,
)
from apps.health.constants import (
    DATABASE_DEPENDENCY,
    DATABASE_INTEGRATION_ERROR,
    DEPENDENCY_ERROR,
    DEPENDENCY_OK,
    HEALTH_OK_MESSAGE,
    SERVICE_UNAVAILABLE_CODE,
)

health_check_schema = extend_schema(
    summary='Check the system and its dependencies',
    description=(
        'Tells whether the system can serve requests and the state of each '
        'dependency it needs (today, the database). Used by the deploy to verify a '
        'release. Public; it has the base request limit.'
    ),
    responses={
        200: success_envelope_schema(
            'HealthCheckOk',
            data=serializers.DictField(child=serializers.CharField()),
        ),
        429: error_envelope_schema('HealthCheckRateLimited', detail=ERROR_CODE_DETAIL),
        500: error_envelope_schema('HealthCheckFailed', detail=INTERNAL_ERROR_DETAIL),
        503: error_envelope_schema(
            'HealthCheckUnavailable',
            detail=serializers.DictField(child=serializers.CharField()),
        ),
    },
    examples=[
        success_example(
            'System healthy',
            {DATABASE_DEPENDENCY: DEPENDENCY_OK},
            message=HEALTH_OK_MESSAGE,
        ),
        error_example(
            'Too many requests',
            HTTPStatus.TOO_MANY_REQUESTS,
            RATE_LIMITED_MESSAGE,
            {'code': RATE_LIMITED_CODE},
        ),
        INTERNAL_ERROR_EXAMPLE,
        error_example(
            'Database unavailable',
            HTTPStatus.SERVICE_UNAVAILABLE,
            DATABASE_INTEGRATION_ERROR,
            {'code': SERVICE_UNAVAILABLE_CODE, DATABASE_DEPENDENCY: DEPENDENCY_ERROR},
        ),
    ],
)
