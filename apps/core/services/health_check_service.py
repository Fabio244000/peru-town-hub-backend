from apps.core.constants import (
    HEALTH_DETAIL_OK,
    HEALTH_ERRORS_SEPARATOR,
    HEALTH_STATUS_ERROR,
    HEALTH_STATUS_OK,
)
from apps.core.domain.entities.health_status import HealthStatus
from apps.core.domain.interfaces.dependencies_check_interface import (
    DependenciesCheckInterface,
)


class HealthCheckService:
    def __init__(self, dependencies_check: DependenciesCheckInterface):
        self._dependencies_check = dependencies_check

    def get_health_status(self) -> HealthStatus:
        result = self._dependencies_check.check_dependencies()

        if result.is_healthy:
            return HealthStatus(
                is_healthy=True, status=HEALTH_STATUS_OK, detail=HEALTH_DETAIL_OK
            )
        return HealthStatus(
            is_healthy=False,
            status=HEALTH_STATUS_ERROR,
            detail=HEALTH_ERRORS_SEPARATOR.join(result.errors),
        )
