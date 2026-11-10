from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from apps.locations.models import Department, District, PopulatedCenter, Province

pytestmark = pytest.mark.django_db

LOCATION_MODELS = (Department, Province, District, PopulatedCenter)
AYACUCHO_LOADED = (
    'Departamentos: 1\nProvincias: 11\nDistritos: 124\nCentros poblados: 7419\n'
)


def load_locations(*args: str) -> str:
    output = StringIO()
    call_command('load_locations', *args, stdout=output)
    return output.getvalue()


def test_loads_every_location_of_ayacucho_from_the_catalog():
    assert load_locations() == AYACUCHO_LOADED


def test_loads_each_location_under_the_one_it_belongs_to():
    load_locations()

    pincocalla = PopulatedCenter.objects.get(code='0509060019')
    assert pincocalla.name == 'Pincocalla'
    assert pincocalla.district.name == 'Morcolla'
    assert pincocalla.district.province.name == 'Sucre'
    assert pincocalla.district.province.department.name == 'Ayacucho'


def test_loads_no_location_of_another_department():
    load_locations()

    assert not any(
        model.objects.exclude(code__startswith='05').exists()
        for model in LOCATION_MODELS
    )


def test_reloading_repeats_nothing():
    load_locations()

    assert load_locations() == AYACUCHO_LOADED
    assert PopulatedCenter.objects.count() == 7419


def test_reports_a_load_error_and_saves_nothing(tmp_path):
    with pytest.raises(CommandError, match='No existe el archivo'):
        load_locations('--path', str(tmp_path / 'missing.yaml'))

    assert not any(model.objects.exists() for model in LOCATION_MODELS)
