from dataclasses import dataclass


@dataclass(frozen=True)
class DependenciesCheckResult:
    is_healthy: bool
    errors: tuple[str, ...]
