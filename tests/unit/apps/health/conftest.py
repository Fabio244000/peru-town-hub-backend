import pytest

from apps.health.integrations.dependencies_check.port import (
    DependenciesCheck,
    DependenciesCheckResult,
)


class FakeDependenciesCheck(DependenciesCheck):
    def __init__(self, statuses, errors=()):
        self._result = DependenciesCheckResult(statuses=statuses, errors=tuple(errors))

    def check_dependencies(self):
        return self._result


@pytest.fixture
def fake_dependencies_check():
    return FakeDependenciesCheck
