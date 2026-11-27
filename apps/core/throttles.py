from typing import TYPE_CHECKING

from django.conf import settings
from rest_framework import exceptions
from rest_framework.request import Request
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

# DRF imports this module (DEFAULT_THROTTLE_CLASSES) while it defines APIView, so
# APIView may only be imported for type checking here.
if TYPE_CHECKING:
    from rest_framework.views import APIView


class RateLimited(exceptions.Throttled):
    """A request limit that answers with its own message."""

    def __init__(self, message: str, wait: float | None) -> None:
        super().__init__(wait=wait)
        self.message = message


class BaseAnonRateThrottle(AnonRateThrottle):
    """The base limit of every anonymous request, per IP (security.md §2)."""

    def get_rate(self) -> str:
        return f'{settings.API_ANON_RATE_PER_MINUTE}/min'


class BaseUserRateThrottle(UserRateThrottle):
    """The base limit of every authenticated request, per user."""

    def get_rate(self) -> str:
        return f'{settings.API_USER_RATE_PER_MINUTE}/min'

    def get_cache_key(self, request: Request, view: 'APIView') -> str | None:
        # An anonymous request already has its limit per IP.
        if not request.user or not request.user.is_authenticated:
            return None
        return super().get_cache_key(request, view)
