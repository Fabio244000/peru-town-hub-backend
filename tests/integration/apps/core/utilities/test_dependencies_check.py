import pytest
from django.db import OperationalError
from django.db.backends.base.base import BaseDatabaseWrapper

from apps.core.constants import DATABASE_INTEGRATION_ERROR
from apps.core.utilities.dependencies_check import DependenciesCheck


@pytest.mark.django_db
def test_dependencies_are_healthy_when_database_is_available():
    result = DependenciesCheck().check_dependencies()

    assert result.is_healthy is True
    assert result.errors == ()


def test_reports_database_error_when_database_is_unavailable(monkeypatch):
    def fail_to_connect(self):
        raise OperationalError('connection refused')

    monkeypatch.setattr(BaseDatabaseWrapper, 'ensure_connection', fail_to_connect)

    result = DependenciesCheck().check_dependencies()

    assert result.is_healthy is False
    assert result.errors == (DATABASE_INTEGRATION_ERROR,)
