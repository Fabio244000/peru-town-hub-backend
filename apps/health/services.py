from apps.core.exceptions import ServiceUnavailableError
from apps.health.constants import HEALTH_ERROR_SEPARATOR
from apps.health.integrations.dependencies_check import get_dependencies_check
from apps.health.integrations.dependencies_check.port import DependenciesCheck


class HealthCheckService:
    def __init__(self, dependencies_check: DependenciesCheck | None = None) -> None:
        self._dependencies_check = dependencies_check or get_dependencies_check()

    def check(self) -> dict[str, str]:
        result = self._dependencies_check.check_dependencies()

        if not result.is_healthy:
            raise ServiceUnavailableError(
                HEALTH_ERROR_SEPARATOR.join(result.errors), detail=result.statuses
            )
        return result.statuses
