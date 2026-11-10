from pathlib import Path

from django.core.management.base import BaseCommand, CommandError, CommandParser

from apps.core.exceptions import ApplicationError
from apps.locations.constants import (
    AYACUCHO_CATALOG_PATH,
    CATALOG_PATH_HELP,
    LEVEL_LOADED,
    LOAD_LOCATIONS_HELP,
)
from apps.locations.services import LocationCatalogService


class Command(BaseCommand):
    help = LOAD_LOCATIONS_HELP

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            '--path', type=Path, default=AYACUCHO_CATALOG_PATH, help=CATALOG_PATH_HELP
        )

    def handle(self, *args: str, path: Path, **options: object) -> None:
        try:
            loaded = LocationCatalogService().load(path=path)
        except ApplicationError as error:
            raise CommandError(error.message) from error
        for level, count in loaded.items():
            self.stdout.write(
                LEVEL_LOADED.format(level=level.capitalize(), count=count)
            )
