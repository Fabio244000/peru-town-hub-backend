from abc import ABC, abstractmethod

from apps.core.domain.entities.dependencies_check_result import (
    DependenciesCheckResult,
)


class DependenciesCheckInterface(ABC):
    @abstractmethod
    def check_dependencies(self) -> DependenciesCheckResult: ...
