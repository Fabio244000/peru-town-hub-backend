import re
from decimal import Decimal

import pytest

from apps.core.exceptions import ApplicationError
from apps.locations.constants import (
    CATALOG_NOT_FOUND,
    CATALOG_UNREADABLE,
    CODE_REPEATED,
    LOCATION_INVALID,
)
from apps.locations.services import LocationCatalogService
from tests.factories.locations import PopulatedCenterFactory

pytestmark = pytest.mark.django_db


def valid_catalog() -> dict:
    """Ayacucho → Sucre → Morcolla → Pincocalla (with coordinates) and Chumbes (without)."""
    return {
        'code': '050000',
        'name': 'Ayacucho',
        'altitude': 2761,
        'latitude': -13.158,
        'longitude': -74.224,
        'provinces': [
            {
                'code': '050900',
                'name': 'Sucre',
                'districts': [
                    {
                        'code': '050906',
                        'name': 'Morcolla',
                        'altitude': 3200,
                        'populated_centers': [
                            {
                                'code': '0509060019',
                                'name': 'Pincocalla',
                                'type': 'rural',
                                'altitude': 3400,
                                'latitude': -14.104567,
                                'longitude': -73.912345,
                            },
                            {'code': '0509060001', 'name': 'Chumbes', 'type': 'urban'},
                        ],
                    }
                ],
            }
        ],
    }


def populated_center(catalog: dict) -> dict:
    return catalog['provinces'][0]['districts'][0]['populated_centers'][0]


def test_loads_each_location_under_the_one_it_belongs_to(
    write_catalog, stored_location
):
    LocationCatalogService().load(path=write_catalog(valid_catalog()))

    assert stored_location('0509060019')['parent'] == '050906'
    assert stored_location('050906')['parent'] == '050900'
    assert stored_location('050900')['parent'] == '050000'
    assert stored_location('050000')['parent'] is None


def test_returns_how_many_locations_of_each_level_were_loaded(write_catalog):
    loaded = LocationCatalogService().load(path=write_catalog(valid_catalog()))

    assert loaded == {
        'departamentos': 1,
        'provincias': 1,
        'distritos': 1,
        'centros poblados': 2,
    }


def test_stores_the_name_without_surrounding_spaces(write_catalog, stored_location):
    catalog = valid_catalog()
    populated_center(catalog)['name'] = '  Pincocalla '

    LocationCatalogService().load(path=write_catalog(catalog))

    assert stored_location('0509060019')['name'] == 'Pincocalla'


def test_keeps_the_coordinates_and_altitude_the_catalog_has(
    write_catalog, stored_location
):
    LocationCatalogService().load(path=write_catalog(valid_catalog()))

    location = stored_location('0509060019')
    assert location['altitude'] == 3400
    assert location['latitude'] == Decimal('-14.104567')
    assert location['longitude'] == Decimal('-73.912345')


def test_loads_a_location_without_coordinates_or_altitude(
    write_catalog, stored_location
):
    LocationCatalogService().load(path=write_catalog(valid_catalog()))

    location = stored_location('0509060001')
    assert location['altitude'] is None
    assert location['latitude'] is None
    assert location['longitude'] is None


def test_reloading_updates_a_corrected_name_without_repeating_anything(
    write_catalog, stored_location
):
    catalog = valid_catalog()
    LocationCatalogService().load(path=write_catalog(catalog))
    populated_center(catalog)['name'] = 'Pinco Calla'

    loaded = LocationCatalogService().load(path=write_catalog(catalog))

    assert stored_location('0509060019')['name'] == 'Pinco Calla'
    assert loaded['centros poblados'] == 2


def test_reloading_deletes_nothing_missing_from_the_catalog(
    write_catalog, stored_location
):
    catalog = valid_catalog()
    LocationCatalogService().load(path=write_catalog(catalog))
    catalog['provinces'][0]['districts'][0]['populated_centers'].pop()

    LocationCatalogService().load(path=write_catalog(catalog))

    assert stored_location('0509060001') is not None


def test_overwrites_an_edit_made_in_the_admin(write_catalog, stored_location):
    PopulatedCenterFactory(code='0509060019', name='Editado en el admin')

    LocationCatalogService().load(path=write_catalog(valid_catalog()))

    location = stored_location('0509060019')
    assert location['name'] == 'Pincocalla'
    assert location['parent'] == '050906'


def test_rejects_a_missing_file(tmp_path):
    path = tmp_path / 'missing.yaml'

    with pytest.raises(
        ApplicationError, match=re.escape(CATALOG_NOT_FOUND.format(path=path))
    ):
        LocationCatalogService().load(path=path)


def test_rejects_a_badly_written_file_naming_its_line(tmp_path):
    path = tmp_path / 'catalog.yaml'
    path.write_text("code: '050000'\n  name: Ayacucho\n", encoding='utf-8')

    with pytest.raises(
        ApplicationError, match=re.escape(CATALOG_UNREADABLE.format(path=path, line=2))
    ):
        LocationCatalogService().load(path=path)


def test_names_the_location_and_the_field_of_an_invalid_value(write_catalog):
    catalog = valid_catalog()
    populated_center(catalog)['altitude'] = 7001
    expected = LOCATION_INVALID.format(location='0509060019', errors='altitud: ')

    with pytest.raises(ApplicationError, match=f'^{re.escape(expected)}'):
        LocationCatalogService().load(path=write_catalog(catalog))


@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('code', None),
        ('name', None),
        ('name', '   '),
        ('name', 'a' * 251),
        ('code', '050906001'),
        ('code', '05090600AB'),
        ('type', 'mixto'),
        ('altitude', -1),
        ('altitude', 7001),
        ('latitude', -90.000001),
        ('latitude', 90.000001),
        ('longitude', -180.000001),
        ('longitude', 180.000001),
    ],
)
def test_rejects_a_location_with_an_invalid_field(write_catalog, field, value):
    catalog = valid_catalog()
    populated_center(catalog)[field] = value

    with pytest.raises(ApplicationError) as exc_info:
        LocationCatalogService().load(path=write_catalog(catalog))

    assert list(exc_info.value.detail) == [field]


@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('name', 'a' * 250),
        ('altitude', 0),
        ('altitude', 7000),
        ('latitude', -90),
        ('latitude', 90),
        ('longitude', -180),
        ('longitude', 180),
    ],
)
def test_accepts_the_limits_of_each_field(write_catalog, stored_location, field, value):
    catalog = valid_catalog()
    populated_center(catalog)[field] = value

    LocationCatalogService().load(path=write_catalog(catalog))

    assert stored_location('0509060019')[field] == value


def test_rejects_a_repeated_code(write_catalog):
    catalog = valid_catalog()
    centers = catalog['provinces'][0]['districts'][0]['populated_centers']
    centers[1]['code'] = centers[0]['code']

    with pytest.raises(
        ApplicationError, match=re.escape(CODE_REPEATED.format(code='0509060019'))
    ):
        LocationCatalogService().load(path=write_catalog(catalog))


def test_saves_nothing_when_a_location_fails_after_others_were_saved(
    write_catalog, stored_location
):
    catalog = valid_catalog()
    populated_center(catalog)['altitude'] = 7001

    with pytest.raises(ApplicationError):
        LocationCatalogService().load(path=write_catalog(catalog))

    assert stored_location('050000') is None
