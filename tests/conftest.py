from collections.abc import Callable

import pytest
from django.core.cache import cache
from django.core.management import call_command
from pytest_django.fixtures import Settings

from tests.fake_app import FAKE_APP, FAKE_MIGRATIONS


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    cache.clear()


@pytest.fixture
def migrate_fake_app(settings: Settings) -> Callable[[str], None]:
    settings.MIGRATION_MODULES = {FAKE_APP: FAKE_MIGRATIONS}

    def migrate(target: str) -> None:
        call_command('migrate', FAKE_APP, target, verbosity=0)

    return migrate
