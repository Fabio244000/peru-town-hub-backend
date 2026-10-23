import logging
from collections.abc import Callable

from django.db import DatabaseError, connection

from apps.health.constants import (
    DATABASE_DEPENDENCY,
    DATABASE_INTEGRATION_ERROR,
    DEPENDENCY_ERROR,
    DEPENDENCY_OK,
)
from apps.health.integrations.dependencies_check.port import (
    DependenciesCheck,
    DependenciesCheckResult,
)

logger = logging.getLogger(__name__)


class SystemDependenciesCheck(DependenciesCheck):
    def check_dependencies(self) -> DependenciesCheckResult:
        errors_by_dependency = {name: check() for name, check in self._checks().items()}
        statuses = {
            name: DEPENDENCY_ERROR if error else DEPENDENCY_OK
            for name, error in errors_by_dependency.items()
        }
        errors = tuple(error for error in errors_by_dependency.values() if error)

        return DependenciesCheckResult(statuses=statuses, errors=errors)

    def _checks(self) -> dict[str, Callable[[], str | None]]:
        return {
            DATABASE_DEPENDENCY: self._check_database,
        }

    def _check_database(self) -> str | None:
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except DatabaseError:
            logger.exception('Database integration check failed')
            return DATABASE_INTEGRATION_ERROR
        return None
