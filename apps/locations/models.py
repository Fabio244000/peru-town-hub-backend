from django.core.validators import RegexValidator
from django.db import models

from apps.common.models import BaseModel
from apps.common.validators import range_validators
from apps.locations.constants import (
    ALTITUDE_LABEL,
    ALTITUDE_RANGE,
    CODE_LABEL,
    DEPARTMENT_LABEL,
    DEPARTMENTS_LABEL,
    DISTRICT_LABEL,
    DISTRICTS_LABEL,
    DIVISION_CODE_LENGTH,
    DIVISION_CODE_PATTERN,
    LATITUDE_LABEL,
    LATITUDE_RANGE,
    LONGITUDE_LABEL,
    LONGITUDE_RANGE,
    NAME_LABEL,
    NAME_MAX_LENGTH,
    POPULATED_CENTER_CODE_LENGTH,
    POPULATED_CENTER_CODE_PATTERN,
    POPULATED_CENTER_LABEL,
    POPULATED_CENTERS_LABEL,
    PROVINCE_LABEL,
    PROVINCES_LABEL,
    TYPE_LABEL,
    PopulatedCenterType,
)


def code_field(length: int, pattern: str) -> models.CharField:
    return models.CharField(
        CODE_LABEL, max_length=length, validators=[RegexValidator(pattern)]
    )


def location_constraints(code_pattern: str) -> list[models.BaseConstraint]:
    """The rules every location keeps in the database, named per table."""
    return [
        models.UniqueConstraint(
            fields=['code'], name='%(app_label)s_%(class)s_code_unique'
        ),
        models.CheckConstraint(
            condition=models.Q(code__regex=code_pattern),
            name='%(app_label)s_%(class)s_code_pattern',
        ),
        models.CheckConstraint(
            condition=~models.Q(name=''), name='%(app_label)s_%(class)s_name_not_blank'
        ),
        models.CheckConstraint(
            condition=models.Q(altitude__range=ALTITUDE_RANGE),
            name='%(app_label)s_%(class)s_altitude_range',
        ),
        models.CheckConstraint(
            condition=models.Q(latitude__range=LATITUDE_RANGE),
            name='%(app_label)s_%(class)s_latitude_range',
        ),
        models.CheckConstraint(
            condition=models.Q(longitude__range=LONGITUDE_RANGE),
            name='%(app_label)s_%(class)s_longitude_range',
        ),
    ]


class Location(BaseModel):
    name = models.CharField(NAME_LABEL, max_length=NAME_MAX_LENGTH)
    altitude = models.IntegerField(
        ALTITUDE_LABEL,
        null=True,
        blank=True,
        validators=range_validators(ALTITUDE_RANGE),
    )
    latitude = models.DecimalField(
        LATITUDE_LABEL,
        max_digits=8,
        decimal_places=6,
        null=True,
        blank=True,
        validators=range_validators(LATITUDE_RANGE),
    )
    longitude = models.DecimalField(
        LONGITUDE_LABEL,
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=range_validators(LONGITUDE_RANGE),
    )

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f'{self.name} ({self.code})'


class Department(Location):
    code = code_field(DIVISION_CODE_LENGTH, DIVISION_CODE_PATTERN)

    class Meta:
        verbose_name = DEPARTMENT_LABEL
        verbose_name_plural = DEPARTMENTS_LABEL
        constraints = location_constraints(DIVISION_CODE_PATTERN)


class Province(Location):
    code = code_field(DIVISION_CODE_LENGTH, DIVISION_CODE_PATTERN)
    department = models.ForeignKey(
        Department, models.PROTECT, verbose_name=DEPARTMENT_LABEL
    )

    class Meta:
        verbose_name = PROVINCE_LABEL
        verbose_name_plural = PROVINCES_LABEL
        constraints = location_constraints(DIVISION_CODE_PATTERN)


class District(Location):
    code = code_field(DIVISION_CODE_LENGTH, DIVISION_CODE_PATTERN)
    province = models.ForeignKey(Province, models.PROTECT, verbose_name=PROVINCE_LABEL)

    class Meta:
        verbose_name = DISTRICT_LABEL
        verbose_name_plural = DISTRICTS_LABEL
        constraints = location_constraints(DIVISION_CODE_PATTERN)


class PopulatedCenter(Location):
    code = code_field(POPULATED_CENTER_CODE_LENGTH, POPULATED_CENTER_CODE_PATTERN)
    district = models.ForeignKey(District, models.PROTECT, verbose_name=DISTRICT_LABEL)
    type = models.CharField(
        TYPE_LABEL,
        max_length=max(map(len, PopulatedCenterType.values)),
        choices=PopulatedCenterType.choices,
    )

    class Meta:
        verbose_name = POPULATED_CENTER_LABEL
        verbose_name_plural = POPULATED_CENTERS_LABEL
        constraints = [
            *location_constraints(POPULATED_CENTER_CODE_PATTERN),
            models.CheckConstraint(
                condition=models.Q(type__in=PopulatedCenterType.values),
                name='locations_populatedcenter_type_valid',
            ),
        ]
