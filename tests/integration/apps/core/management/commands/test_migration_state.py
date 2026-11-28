import json
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from apps.core.constants import (
    MIGRATION_IRREVERSIBLE_EXIT_CODE,
    NO_MIGRATIONS_REVERTED,
)
from tests.fake_app import FAKE_APP

pytestmark = pytest.mark.django_db


def migration_state(*args: str) -> str:
    output = StringIO()
    call_command('migration_state', *args, stdout=output)
    return output.getvalue()


def test_record_prints_the_state_as_one_json_line(migrate_fake_app):
    migrate_fake_app('0003_reversible')

    output = migration_state('record')

    assert output.count('\n') == 1
    assert json.loads(output)[FAKE_APP] == '0003_reversible'


def test_restore_prints_each_reverted_app(migrate_fake_app):
    migrate_fake_app('0002_irreversible')
    state = migration_state('record')
    migrate_fake_app('0003_reversible')

    output = migration_state('restore', state)

    assert output == f'{FAKE_APP} 0003_reversible → 0002_irreversible\n'


def test_restore_says_so_when_nothing_was_reverted(migrate_fake_app):
    migrate_fake_app('0003_reversible')
    state = migration_state('record')

    output = migration_state('restore', state)

    assert output == f'{NO_MIGRATIONS_REVERTED}\n'


def test_restore_exits_with_its_own_code_when_a_migration_cannot_go_back(
    migrate_fake_app,
):
    migrate_fake_app('0001_initial')
    state = migration_state('record')
    migrate_fake_app('0003_reversible')

    with pytest.raises(CommandError, match='0002_irreversible') as error:
        migration_state('restore', state)

    assert error.value.returncode == MIGRATION_IRREVERSIBLE_EXIT_CODE
