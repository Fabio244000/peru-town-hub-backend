from datetime import datetime, timedelta
from math import ceil
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.throttling import BaseThrottle, SimpleRateThrottle
from rest_framework.views import APIView

from apps.accounts.constants import (
    SIGNUP_HOURLY_LIMIT_REACHED,
    SIGNUP_MONTHLY_LIMIT_REACHED,
)
from apps.core.constants import BUSINESS_TIME_ZONE


class SignupHourlyThrottle(SimpleRateThrottle):
    """R8, L6: sign-up requests of a device (its IP) in the last hour."""

    scope = 'signup_hourly'

    def get_rate(self) -> str:
        return f'{settings.SIGNUP_RATE_PER_HOUR}/hour'

    def get_cache_key(self, request: Request, view: APIView) -> str:
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }

    @property
    def message(self) -> str:
        return SIGNUP_HOURLY_LIMIT_REACHED.format(support_email=settings.SUPPORT_EMAIL)


class SignupMonthlyThrottle(BaseThrottle):
    """R8, L6: sign-up requests of a device in the calendar month, Peru's time.

    DRF's rates only know seconds to days, and a sliding window would not match
    "try again next month": this one starts again on the 1st.
    """

    scope = 'signup_monthly'

    def allow_request(self, request: Request, view: APIView) -> bool:
        now = timezone.localtime(timezone.now(), ZoneInfo(BUSINESS_TIME_ZONE))
        self._wait = (self._next_month(now) - now).total_seconds()
        key = f'throttle_{self.scope}_{self.get_ident(request)}_{now:%Y-%m}'
        cache.add(key, 0, timeout=ceil(self._wait))
        return cache.incr(key) <= settings.SIGNUP_RATE_PER_MONTH

    def wait(self) -> float:
        return self._wait

    @property
    def message(self) -> str:
        return SIGNUP_MONTHLY_LIMIT_REACHED.format(support_email=settings.SUPPORT_EMAIL)

    def _next_month(self, now: datetime) -> datetime:
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return (start_of_month + timedelta(days=32)).replace(day=1)


class UsernameCheckThrottle(SimpleRateThrottle):
    """Checks of a username by a device (its IP) per minute; the generic message."""

    scope = 'username_check'

    def get_rate(self) -> str:
        return f'{settings.USERNAME_CHECK_RATE_PER_MINUTE}/min'

    def get_cache_key(self, request: Request, view: APIView) -> str:
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }
