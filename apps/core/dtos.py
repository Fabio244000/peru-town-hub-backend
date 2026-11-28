from dataclasses import dataclass


@dataclass(frozen=True)
class MigrationChange:
    app_label: str
    before: str
    after: str
