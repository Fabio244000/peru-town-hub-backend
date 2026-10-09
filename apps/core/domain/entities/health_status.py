from dataclasses import dataclass


@dataclass(frozen=True)
class HealthStatus:
    is_healthy: bool
    status: str
    detail: str
