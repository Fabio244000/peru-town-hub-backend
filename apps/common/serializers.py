from datetime import UTC
from typing import Any

from rest_framework import serializers


class UtcDateTimeField(serializers.DateTimeField):
    """ISO 8601 in UTC with Z (conventions/contracts.md §3), whatever TIME_ZONE is."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(default_timezone=UTC, **kwargs)
