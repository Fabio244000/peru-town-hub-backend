from rest_framework import exceptions
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.core.throttles import RateLimited


class ThrottleMessageMixin(APIView):
    """Stops at the first limit reached and answers with that limit's message.

    DRF only reports how long to wait, not which limit failed.
    """

    def check_throttles(self, request: Request) -> None:
        for throttle in self.get_throttles():
            if not throttle.allow_request(request, self):
                message = getattr(throttle, 'message', '')
                wait = throttle.wait()
                raise (
                    RateLimited(message, wait)
                    if message
                    else exceptions.Throttled(wait)
                )
