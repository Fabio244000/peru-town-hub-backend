from collections import Counter
from datetime import datetime
from pathlib import Path

import yaml
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import ApplicationError
from apps.locations.constants import (
    BULK_BATCH_SIZE,
    CATALOG_NOT_FOUND,
    CATALOG_UNREADABLE,
    CODE_REPEATED,
    DEPARTMENTS_LABEL,
    DISTRICTS_LABEL,
    LOCATION_INVALID,
    POPULATED_CENTERS_LABEL,
    PROVINCES_LABEL,
)
from apps.locations.models import (
    Department,
    District,
    Location,
    PopulatedCenter,
    Province,
)

LOCATION_FIELDS = ('code', 'name', 'altitude', 'latitude', 'longitude')
FIELDS = {
    Department: LOCATION_FIELDS,
    Province: LOCATION_FIELDS,
    District: LOCATION_FIELDS,
    PopulatedCenter: (*LOCATION_FIELDS, 'type'),
}
PARENT_FIELD = {
    Department: None,
    Province: 'department',
    District: 'province',
    PopulatedCenter: 'district',
}

# A record of the YAML with the location it belongs to (before saving) or with its
# own location (after saving).
Entry = tuple[dict, Location | None]


class LocationCatalogService:
    """Loads the catalog of locations, each one under the one it belongs to."""

    @transaction.atomic
    def load(self, *, path: Path) -> dict[str, int]:
        """Adds or updates by code what the catalog has; deletes nothing."""
        now = timezone.now()
        department = self._read(path)
        departments = self._save_level(Department, [(department, None)], now)
        provinces = self._save_level(
            Province, self._children(departments, 'provinces'), now
        )
        districts = self._save_level(
            District, self._children(provinces, 'districts'), now
        )
        centers = self._save_level(
            PopulatedCenter, self._children(districts, 'populated_centers'), now
        )
        return {
            DEPARTMENTS_LABEL: len(departments),
            PROVINCES_LABEL: len(provinces),
            DISTRICTS_LABEL: len(districts),
            POPULATED_CENTERS_LABEL: len(centers),
        }

    def _read(self, path: Path) -> dict:
        try:
            with path.open(encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError as error:
            raise ApplicationError(CATALOG_NOT_FOUND.format(path=path)) from error
        except yaml.MarkedYAMLError as error:
            line = error.problem_mark.line + 1
            message = CATALOG_UNREADABLE.format(path=path, line=line)
            raise ApplicationError(message) from error

    def _save_level(
        self, model: type[Location], entries: list[Entry], now: datetime
    ) -> list[Entry]:
        locations = [
            self._build(model, record, parent, now) for record, parent in entries
        ]
        self._ensure_unique_codes(locations)
        self._upsert(model, locations)
        return [
            (record, location)
            for (record, _), location in zip(entries, locations, strict=True)
        ]

    def _build(
        self,
        model: type[Location],
        record: dict,
        parent: Location | None,
        now: datetime,
    ) -> Location:
        values = {field: self._yaml_value(record.get(field)) for field in FIELDS[model]}
        if isinstance(values['name'], str):
            values['name'] = values['name'].strip()
        if PARENT_FIELD[model]:
            values[PARENT_FIELD[model]] = parent
        location = model(**values, created_at=now, updated_at=now)
        self._validate(location)
        return location

    def _yaml_value(self, value: object) -> object:
        # Django pads a float with zeros up to the field's precision (-74.224 becomes
        # -74.2240000); as text the decimal keeps the places the YAML gives.
        return str(value) if isinstance(value, float) else value

    def _validate(self, location: Location) -> None:
        # The parent comes from the catalog itself, and uniqueness is checked in memory.
        parent_field = PARENT_FIELD[type(location)]
        try:
            location.full_clean(
                exclude=[parent_field] if parent_field else None,
                validate_unique=False,
                validate_constraints=False,
            )
        except ValidationError as error:
            errors = '; '.join(
                f'{location._meta.get_field(field).verbose_name}: {" ".join(messages)}'
                for field, messages in error.message_dict.items()
            )
            message = LOCATION_INVALID.format(
                location=location.code or location.name, errors=errors
            )
            raise ApplicationError(message, detail=error.message_dict) from error

    def _ensure_unique_codes(self, locations: list[Location]) -> None:
        for code, count in Counter(location.code for location in locations).items():
            if count > 1:
                raise ApplicationError(CODE_REPEATED.format(code=code))

    def _upsert(self, model: type[Location], locations: list[Location]) -> None:
        parent_field = PARENT_FIELD[model]
        updated = [field for field in FIELDS[model] if field != 'code']
        model.objects.bulk_create(
            locations,
            update_conflicts=True,
            unique_fields=['code'],
            update_fields=[
                *updated,
                'updated_at',
                *([parent_field] if parent_field else []),
            ],
            batch_size=BULK_BATCH_SIZE,
        )

    def _children(self, saved: list[Entry], key: str) -> list[Entry]:
        return [
            (child, location)
            for record, location in saved
            for child in record.get(key) or []
        ]
