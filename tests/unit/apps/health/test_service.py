import pytest

from apps.core.exceptions import ServiceUnavailableError
from apps.health.constants import (
    DATABASE_DEPENDENCY,
    DATABASE_INTEGRATION_ERROR,
    DEPENDENCY_ERROR,
    DEPENDENCY_OK,
)
from apps.health.services import HealthCheckService

OTHER_DEPENDENCY = 'celery'
OTHER_INTEGRATION_ERROR = 'Error en otra integración'


def test_returns_statuses_when_all_dependencies_are_healthy(fake_dependencies_check):
    statuses = {DATABASE_DEPENDENCY: DEPENDENCY_OK}
    service = HealthCheckService(fake_dependencies_check(statuses))

    assert service.check() == statuses


def test_raises_service_unavailable_when_a_dependency_fails(fake_dependencies_check):
    statuses = {DATABASE_DEPENDENCY: DEPENDENCY_ERROR}
    service = HealthCheckService(
        fake_dependencies_check(statuses, errors=[DATABASE_INTEGRATION_ERROR])
    )

    with pytest.raises(ServiceUnavailableError) as exc_info:
        service.check()

    assert exc_info.value.message == DATABASE_INTEGRATION_ERROR
    assert exc_info.value.detail == statuses


def test_joins_all_messages_when_several_dependencies_fail(fake_dependencies_check):
    statuses = {
        DATABASE_DEPENDENCY: DEPENDENCY_ERROR,
        OTHER_DEPENDENCY: DEPENDENCY_ERROR,
    }
    service = HealthCheckService(
        fake_dependencies_check(
            statuses, errors=[DATABASE_INTEGRATION_ERROR, OTHER_INTEGRATION_ERROR]
        )
    )

    with pytest.raises(ServiceUnavailableError) as exc_info:
        service.check()

    assert (
        exc_info.value.message
        == f'{DATABASE_INTEGRATION_ERROR}; {OTHER_INTEGRATION_ERROR}'
    )
    assert exc_info.value.detail == statuses


def test_resolves_the_dependencies_check_by_default(
    fake_dependencies_check, monkeypatch
):
    statuses = {DATABASE_DEPENDENCY: DEPENDENCY_OK}
    monkeypatch.setattr(
        'apps.health.services.get_dependencies_check',
        lambda: fake_dependencies_check(statuses),
    )

    assert HealthCheckService().check() == statuses
