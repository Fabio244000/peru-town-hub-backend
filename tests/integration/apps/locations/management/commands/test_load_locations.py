from io import StringIO
from pathlib import Path

import pytest
import yaml
from django.core.management import CommandError, call_command

from apps.locations.models import Department, District, PopulatedCenter, Province

pytestmark = pytest.mark.django_db

LOCATION_MODELS = (Department, Province, District, PopulatedCenter)
AYACUCHO_LOADED = (
    'Departamentos: 1\nProvincias: 11\nDistritos: 124\nCentros poblados: 7419\n'
)
SMALL_CATALOG = {
    'code': '050000',
    'name': 'Ayacucho',
    'provinces': [
        {
            'code': '050900',
            'name': 'Sucre',
            'districts': [
                {
                    'code': '050906',
                    'name': 'Morcolla',
                    'populated_centers': [
                        {'code': '0509060019', 'name': 'Pincocalla', 'type': 'rural'}
                    ],
                }
            ],
        }
    ],
}
SMALL_CATALOG_LOADED = (
    'Departamentos: 1\nProvincias: 1\nDistritos: 1\nCentros poblados: 1\n'
)


def load_locations(*args: str) -> str:
    output = StringIO()
    call_command('load_locations', *args, stdout=output)
    return output.getvalue()


def write_small_catalog(directory: Path) -> str:
    path = directory / 'catalog.yaml'
    path.write_text(yaml.safe_dump(SMALL_CATALOG), encoding='utf-8')
    return str(path)


def test_loads_the_ayacucho_catalog_as_published():
    """The only test with the real catalog: one load proves the delivered data."""
    output = load_locations()

    assert output == AYACUCHO_LOADED
    pincocalla = PopulatedCenter.objects.get(code='0509060019')
    assert pincocalla.name == 'Pincocalla'
    assert pincocalla.district.name == 'Morcolla'
    assert pincocalla.district.province.name == 'Sucre'
    assert pincocalla.district.province.department.name == 'Ayacucho'
    assert not any(
        model.objects.exclude(code__startswith='05').exists()
        for model in LOCATION_MODELS
    )


def test_reloading_repeats_nothing(tmp_path):
    catalog = write_small_catalog(tmp_path)
    load_locations('--path', catalog)

    assert load_locations('--path', catalog) == SMALL_CATALOG_LOADED
    assert PopulatedCenter.objects.count() == 1


def test_reports_a_load_error_and_saves_nothing(tmp_path):
    with pytest.raises(CommandError, match='No existe el archivo'):
        load_locations('--path', str(tmp_path / 'missing.yaml'))

    assert not any(model.objects.exists() for model in LOCATION_MODELS)
