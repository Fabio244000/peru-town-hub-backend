from collections.abc import Callable
from pathlib import Path

import pytest
import yaml

from apps.locations.models import Department, District, PopulatedCenter, Province

PARENTS = {
    Department: None,
    Province: 'department',
    District: 'province',
    PopulatedCenter: 'district',
}


@pytest.fixture
def write_catalog(tmp_path: Path) -> Callable[[dict], Path]:
    def write(catalog: dict) -> Path:
        path = tmp_path / 'catalog.yaml'
        path.write_text(yaml.safe_dump(catalog, allow_unicode=True), encoding='utf-8')
        return path

    return write


@pytest.fixture
def stored_location() -> Callable[[str], dict | None]:
    """The only place of these tests that reads the models."""

    def read(code: str) -> dict | None:
        for model, parent_field in PARENTS.items():
            location = model.objects.filter(code=code).first()
            if location:
                parent = getattr(location, parent_field) if parent_field else None
                return {
                    'name': location.name,
                    'parent': parent.code if parent else None,
                    'altitude': location.altitude,
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                }
        return None

    return read
