from apps.health.integrations.dependencies_check.port import DependenciesCheck
from apps.health.integrations.dependencies_check.system import (
    SystemDependenciesCheck,
)


def get_dependencies_check() -> DependenciesCheck:
    return SystemDependenciesCheck()
