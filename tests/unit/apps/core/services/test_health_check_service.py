from apps.core.constants import (
    DATABASE_INTEGRATION_ERROR,
    HEALTH_DETAIL_OK,
    HEALTH_STATUS_ERROR,
    HEALTH_STATUS_OK,
)
from apps.core.domain.entities.health_status import HealthStatus
from apps.core.services.health_check_service import HealthCheckService

OTHER_INTEGRATION_ERROR = 'Error en otra integración'


def test_returns_ok_when_all_dependencies_are_healthy(fake_dependencies_check):
    service = HealthCheckService(fake_dependencies_check())

    assert service.get_health_status() == HealthStatus(
        is_healthy=True, status=HEALTH_STATUS_OK, detail=HEALTH_DETAIL_OK
    )


def test_joins_all_errors_when_several_dependencies_fail(fake_dependencies_check):
    service = HealthCheckService(
        fake_dependencies_check(
            errors=[DATABASE_INTEGRATION_ERROR, OTHER_INTEGRATION_ERROR]
        )
    )

    assert service.get_health_status() == HealthStatus(
        is_healthy=False,
        status=HEALTH_STATUS_ERROR,
        detail=f'{DATABASE_INTEGRATION_ERROR}; {OTHER_INTEGRATION_ERROR}',
    )
