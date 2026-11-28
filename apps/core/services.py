from django.db import connection
from django.db.migrations import Migration
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.loader import MigrationLoader

from apps.core.constants import (
    MIGRATION_IRREVERSIBLE,
    MIGRATION_IRREVERSIBLE_CODE,
    MIGRATION_ZERO,
)
from apps.core.dtos import MigrationChange
from apps.core.exceptions import ApplicationError

# App label -> its last applied migration, or MIGRATION_ZERO.
MigrationState = dict[str, str]


class MigrationStateService:
    def record(self) -> MigrationState:
        loader = MigrationLoader(connection)
        return {
            app_label: self._last_applied(loader, app_label)
            for app_label in sorted(loader.migrated_apps)
        }

    def restore(self, *, state: MigrationState) -> tuple[MigrationChange, ...]:
        before = self.record()
        executor = MigrationExecutor(connection)
        targets = [
            (app_label, None if name == MIGRATION_ZERO else name)
            for app_label, name in state.items()
        ]
        plan = executor.migration_plan(targets)
        self._ensure_reversible(plan)
        executor.migrate(targets, plan=plan)
        after = self.record()
        return tuple(
            MigrationChange(app_label=app_label, before=before[app_label], after=name)
            for app_label, name in after.items()
            if before[app_label] != name
        )

    def _last_applied(self, loader: MigrationLoader, app_label: str) -> str:
        applied = [
            key
            for key in loader.applied_migrations
            if key[0] == app_label and key in loader.graph.nodes
        ]
        if not applied:
            return MIGRATION_ZERO
        # The last one is the applied migration that has the others as ancestors.
        return max(applied, key=lambda key: len(loader.graph.forwards_plan(key)))[1]

    def _ensure_reversible(self, plan: list[tuple[Migration, bool]]) -> None:
        for migration, backwards in plan:
            if backwards and not all(op.reversible for op in migration.operations):
                raise ApplicationError(
                    MIGRATION_IRREVERSIBLE.format(
                        migration=f'{migration.app_label} {migration.name}'
                    ),
                    MIGRATION_IRREVERSIBLE_CODE,
                )
