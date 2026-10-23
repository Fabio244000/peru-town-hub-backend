from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class DependenciesCheckResult:
    statuses: dict[str, str]
    errors: tuple[str, ...]

    @property
    def is_healthy(self) -> bool:
        return not self.errors


class DependenciesCheck(ABC):
    @abstractmethod
    def check_dependencies(self) -> DependenciesCheckResult: ...
