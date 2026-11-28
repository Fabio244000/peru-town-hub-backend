from .base import *  # noqa

DEBUG = True

# The migration linter runs only where its command is needed: locally and in CI.
INSTALLED_APPS += ['django_migration_linter']  # noqa: F405
