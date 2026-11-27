from collections.abc import Iterable

import pytest

from apps.health.integrations.dependencies_check.port import (
    DependenciesCheck,
    DependenciesCheckResult,
)


class FakeDependenciesCheck(DependenciesCheck):
    def __init__(self, statuses: dict[str, str], errors: Iterable[str] = ()) -> None:
        self._result = DependenciesCheckResult(statuses=statuses, errors=tuple(errors))

    def check_dependencies(self) -> DependenciesCheckResult:
        return self._result


@pytest.fixture
def fake_dependencies_check() -> type[FakeDependenciesCheck]:
    return FakeDependenciesCheck
