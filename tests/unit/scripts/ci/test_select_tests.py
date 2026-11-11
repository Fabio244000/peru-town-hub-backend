from pathlib import Path

import pytest

from scripts.ci.select_tests import WHOLE_SUITE, select_tests


def make_project(root: Path, imports: dict[str, list[str]], e2e: bool = False) -> None:
    """Modules under apps/ (each importing the listed ones), with their test folders."""
    for module, imported in imports.items():
        (root / 'apps' / module).mkdir(parents=True)
        (root / 'apps' / module / 'services.py').write_text(
            ''.join(
                f'from apps.{other}.services import service\n' for other in imported
            )
        )
        for kind in ('unit', 'integration'):
            (root / 'tests' / kind / 'apps' / module).mkdir(parents=True)
    if e2e:
        (root / 'tests' / 'e2e').mkdir(parents=True)


def module_tests(*modules: str) -> list[str]:
    return [
        f'tests/{kind}/apps/{module}'
        for module in modules
        for kind in ('unit', 'integration')
    ]


def test_runs_the_tests_of_the_changed_module(tmp_path):
    make_project(tmp_path, {'locations': [], 'accounts': []})

    selected = select_tests(['apps/locations/services.py'], tmp_path)

    assert selected == module_tests('locations')


def test_runs_the_tests_of_a_module_whose_tests_changed(tmp_path):
    make_project(tmp_path, {'locations': [], 'accounts': []})

    selected = select_tests(['tests/unit/apps/accounts/test_models.py'], tmp_path)

    assert selected == module_tests('accounts')


@pytest.mark.parametrize(
    'import_line',
    [
        'from apps.locations.services import LocationCatalogService\n',
        'import apps.locations.models\n',
        'from apps import locations\n',
    ],
)
def test_adds_the_modules_that_depend_on_the_changed_one(tmp_path, import_line):
    make_project(tmp_path, {'locations': [], 'accounts': [], 'experiences': []})
    (tmp_path / 'apps' / 'experiences' / 'services.py').write_text(import_line)

    selected = select_tests(['apps/locations/models.py'], tmp_path)

    assert selected == module_tests('experiences', 'locations')


def test_adds_the_modules_that_depend_on_it_indirectly(tmp_path):
    make_project(
        tmp_path,
        {'locations': [], 'experiences': ['locations'], 'reports': ['experiences']},
    )

    selected = select_tests(['apps/locations/models.py'], tmp_path)

    assert selected == module_tests('experiences', 'locations', 'reports')


@pytest.mark.parametrize(
    'changed', ['apps/core/exceptions.py', 'apps/common/models.py']
)
def test_runs_the_whole_suite_when_a_shared_module_changes(tmp_path, changed):
    make_project(tmp_path, {'core': [], 'common': [], 'locations': []})

    assert select_tests([changed, 'apps/locations/models.py'], tmp_path) == WHOLE_SUITE


@pytest.mark.parametrize(
    'changed',
    [
        'requirements/base.txt',
        'config/settings/base.py',
        'compose/django/Dockerfile',
        'docker-compose.yml',
        '.github/workflows/ci.yml',
        'scripts/ci/select_tests.py',
        'tests/factories/accounts.py',
        'pyproject.toml',
    ],
)
def test_runs_the_whole_suite_when_a_file_outside_a_module_changes(tmp_path, changed):
    make_project(tmp_path, {'locations': []})

    assert select_tests(['apps/locations/models.py', changed], tmp_path) == WHOLE_SUITE


def test_always_adds_the_e2e_tests_when_they_exist(tmp_path):
    make_project(tmp_path, {'locations': []}, e2e=True)

    selected = select_tests(['apps/locations/models.py'], tmp_path)

    assert selected == [*module_tests('locations'), 'tests/e2e']


def test_runs_only_the_e2e_tests_when_only_they_changed(tmp_path):
    make_project(tmp_path, {'locations': []}, e2e=True)

    assert select_tests(['tests/e2e/test_share.py'], tmp_path) == ['tests/e2e']


def test_runs_the_whole_suite_when_nothing_else_would_run(tmp_path):
    make_project(tmp_path, {'locations': []})
    (tmp_path / 'tests' / 'unit' / 'apps' / 'locations').rmdir()
    (tmp_path / 'tests' / 'integration' / 'apps' / 'locations').rmdir()

    assert select_tests(['apps/locations/models.py'], tmp_path) == WHOLE_SUITE
