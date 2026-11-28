import pytest

from apps.core.constants import MIGRATION_IRREVERSIBLE_CODE, MIGRATION_ZERO
from apps.core.dtos import MigrationChange
from apps.core.exceptions import ApplicationError
from apps.core.services import MigrationStateService
from tests.fake_app import FAKE_APP

pytestmark = pytest.mark.django_db


def test_record_gives_the_last_applied_migration_of_every_app(migrate_fake_app):
    migrate_fake_app('0003_reversible')

    state = MigrationStateService().record()

    assert state[FAKE_APP] == '0003_reversible'
    assert {'accounts', 'auth', 'token_blacklist'} <= state.keys()


def test_record_gives_zero_for_an_app_without_applied_migrations(migrate_fake_app):
    migrate_fake_app(MIGRATION_ZERO)

    state = MigrationStateService().record()

    assert state[FAKE_APP] == MIGRATION_ZERO


def test_restore_reverts_what_was_applied_after_the_state(migrate_fake_app):
    migrate_fake_app('0002_irreversible')
    service = MigrationStateService()
    state = service.record()
    migrate_fake_app('0003_reversible')

    changes = service.restore(state=state)

    assert changes == (
        MigrationChange(
            app_label=FAKE_APP, before='0003_reversible', after='0002_irreversible'
        ),
    )
    assert service.record() == state


def test_restore_takes_an_app_back_to_zero(migrate_fake_app):
    migrate_fake_app(MIGRATION_ZERO)
    service = MigrationStateService()
    state = service.record()
    migrate_fake_app('0001_initial')

    changes = service.restore(state=state)

    assert changes == (
        MigrationChange(
            app_label=FAKE_APP, before='0001_initial', after=MIGRATION_ZERO
        ),
    )
    assert service.record() == state


def test_restore_changes_nothing_when_the_state_is_current(migrate_fake_app):
    migrate_fake_app('0003_reversible')
    service = MigrationStateService()
    state = service.record()

    changes = service.restore(state=state)

    assert changes == ()
    assert service.record() == state


def test_restore_reverts_nothing_when_a_migration_cannot_go_back(migrate_fake_app):
    migrate_fake_app('0001_initial')
    service = MigrationStateService()
    state = service.record()
    migrate_fake_app('0003_reversible')

    with pytest.raises(ApplicationError, match='0002_irreversible') as error:
        service.restore(state=state)

    assert error.value.code == MIGRATION_IRREVERSIBLE_CODE
    assert service.record()[FAKE_APP] == '0003_reversible'
