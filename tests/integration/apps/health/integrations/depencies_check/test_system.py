import pytest
from django.db import OperationalError
from django.db.backends.base.base import BaseDatabaseWrapper

from apps.health.constants import (
    DATABASE_DEPENDENCY,
    DATABASE_INTEGRATION_ERROR,
    DEPENDENCY_ERROR,
    DEPENDENCY_OK,
)
from apps.health.integrations.dependencies_check import get_dependencies_check
from apps.health.integrations.dependencies_check.system import (
    SystemDependenciesCheck,
)


@pytest.mark.django_db
def test_database_is_ok_when_it_is_available():
    result = SystemDependenciesCheck().check_dependencies()

    assert result.statuses == {DATABASE_DEPENDENCY: DEPENDENCY_OK}
    assert result.errors == ()
    assert result.is_healthy is True


def test_database_is_reported_as_error_when_it_is_unavailable(monkeypatch, caplog):
    def fail_to_connect(self):
        raise OperationalError('connection refused by db-host')

    monkeypatch.setattr(BaseDatabaseWrapper, 'ensure_connection', fail_to_connect)

    result = SystemDependenciesCheck().check_dependencies()

    assert result.statuses == {DATABASE_DEPENDENCY: DEPENDENCY_ERROR}
    assert result.errors == (DATABASE_INTEGRATION_ERROR,)
    assert result.is_healthy is False
    assert 'connection refused by db-host' in caplog.text


def test_resolver_returns_the_system_adapter():
    assert isinstance(get_dependencies_check(), SystemDependenciesCheck)
