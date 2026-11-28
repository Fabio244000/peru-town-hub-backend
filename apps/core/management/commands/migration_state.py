import json
from typing import cast

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.core.constants import (
    MIGRATION_IRREVERSIBLE_EXIT_CODE,
    MIGRATION_REVERTED,
    MIGRATION_STATE_HELP,
    NO_MIGRATIONS_REVERTED,
    RECORD_HELP,
    RESTORE_HELP,
    STATE_HELP,
)
from apps.core.exceptions import ApplicationError
from apps.core.services import MigrationState, MigrationStateService


class Command(BaseCommand):
    help = MIGRATION_STATE_HELP

    def add_arguments(self, parser: CommandParser) -> None:
        actions = parser.add_subparsers(dest='action', required=True)
        actions.add_parser('record', help=RECORD_HELP)
        restore = actions.add_parser('restore', help=RESTORE_HELP)
        restore.add_argument('state', type=json.loads, help=STATE_HELP)

    def handle(self, *args: str, action: str, **options: object) -> None:
        if action == 'record':
            self._record()
        else:
            self._restore(cast(MigrationState, options['state']))

    def _record(self) -> None:
        self.stdout.write(json.dumps(MigrationStateService().record()))

    def _restore(self, state: MigrationState) -> None:
        try:
            changes = MigrationStateService().restore(state=state)
        except ApplicationError as error:
            raise CommandError(
                error.message, returncode=MIGRATION_IRREVERSIBLE_EXIT_CODE
            ) from error
        for change in changes:
            self.stdout.write(
                MIGRATION_REVERTED.format(
                    app_label=change.app_label, before=change.before, after=change.after
                )
            )
        if not changes:
            self.stdout.write(NO_MIGRATIONS_REVERTED)
