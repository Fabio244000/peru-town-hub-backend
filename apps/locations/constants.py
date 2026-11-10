from pathlib import Path

from django.db import models

AYACUCHO_CATALOG_PATH = Path(__file__).resolve().parent / 'data' / 'ayacucho.yaml'

# Formats and limits (ticket §9.4).
DIVISION_CODE_LENGTH = 6
DIVISION_CODE_PATTERN = r'^[0-9]{6}$'
POPULATED_CENTER_CODE_LENGTH = 10
POPULATED_CENTER_CODE_PATTERN = r'^[0-9]{10}$'
NAME_MAX_LENGTH = 250
ALTITUDE_RANGE = (0, 7000)
LATITUDE_RANGE = (-90, 90)
LONGITUDE_RANGE = (-180, 180)

# Rows per INSERT, under PostgreSQL's limit of query parameters.
BULK_BATCH_SIZE = 1000


class PopulatedCenterType(models.TextChoices):
    URBAN = 'urban', 'urbano'
    RURAL = 'rural', 'rural'


# Admin labels.
CODE_LABEL = 'código'
NAME_LABEL = 'nombre'
ALTITUDE_LABEL = 'altitud'
LATITUDE_LABEL = 'latitud'
LONGITUDE_LABEL = 'longitud'
TYPE_LABEL = 'tipo'
DEPARTMENT_LABEL = 'departamento'
DEPARTMENTS_LABEL = 'departamentos'
PROVINCE_LABEL = 'provincia'
PROVINCES_LABEL = 'provincias'
DISTRICT_LABEL = 'distrito'
DISTRICTS_LABEL = 'distritos'
POPULATED_CENTER_LABEL = 'centro poblado'
POPULATED_CENTERS_LABEL = 'centros poblados'

# Load errors (ticket §9.3).
CATALOG_NOT_FOUND = 'No existe el archivo {path}'
CATALOG_UNREADABLE = 'El archivo {path} está mal escrito (línea {line})'
LOCATION_INVALID = 'La ubicación {location} tiene datos inválidos: {errors}'
CODE_REPEATED = 'El código {code} está repetido'

# load_locations command.
LOAD_LOCATIONS_HELP = 'Carga o actualiza las ubicaciones desde el catálogo (YAML)'
CATALOG_PATH_HELP = 'Ruta del catálogo; por defecto, el de Ayacucho'
LEVEL_LOADED = '{level}: {count}'
