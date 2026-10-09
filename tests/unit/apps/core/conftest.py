import pytest

from apps.core.domain.entities.dependencies_check_result import (
    DependenciesCheckResult,
)
from apps.core.domain.interfaces.dependencies_check_interface import (
    DependenciesCheckInterface,
)


class FakeDependenciesCheck(DependenciesCheckInterface):
    def __init__(self, errors=()):
        self._errors = tuple(errors)

    def check_dependencies(self):
        return DependenciesCheckResult(is_healthy=not self._errors, errors=self._errors)


@pytest.fixture
def fake_dependencies_check():
    return FakeDependenciesCheck
