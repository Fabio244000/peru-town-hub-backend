import logging

from django.db import DatabaseError, connection

from apps.core.constants import DATABASE_INTEGRATION_ERROR
from apps.core.domain.entities.dependencies_check_result import (
    DependenciesCheckResult,
)
from apps.core.domain.interfaces.dependencies_check_interface import (
    DependenciesCheckInterface,
)

logger = logging.getLogger(__name__)


class DependenciesCheck(DependenciesCheckInterface):
    def check_dependencies(self) -> DependenciesCheckResult:
        checks = (self._check_database(),)
        errors = tuple(error for error in checks if error)

        return DependenciesCheckResult(is_healthy=not errors, errors=errors)

    def _check_database(self) -> str | None:
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except DatabaseError:
            logger.exception('Database integration check failed')
            return DATABASE_INTEGRATION_ERROR
        return None
