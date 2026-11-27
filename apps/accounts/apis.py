from http import HTTPStatus

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.throttling import BaseThrottle

from apps.accounts.apidocs.accounts import (
    account_create_schema,
    username_availability_schema,
)
from apps.accounts.dtos import NewAccount
from apps.accounts.selectors import username_is_available
from apps.accounts.serializers import (
    AccountCreateInputSerializer,
    AccountCreateOutputSerializer,
    UsernameAvailabilityInputSerializer,
    UsernameAvailabilityOutputSerializer,
)
from apps.accounts.services import AccountRegistrationService
from apps.accounts.throttles import (
    SignupHourlyThrottle,
    SignupMonthlyThrottle,
    UsernameCheckThrottle,
)
from apps.core.mixins import ThrottleMessageMixin
from apps.core.responses import SuccessResponse

# Each action's own limits replace the base ones; only signing up counts for R8.
ACTION_THROTTLES: dict[str, tuple[type[BaseThrottle], ...]] = {
    'create': (SignupHourlyThrottle, SignupMonthlyThrottle),
    'username_availability': (UsernameCheckThrottle,),
}


class AccountViewSet(ThrottleMessageMixin, viewsets.ViewSet):
    """The person's account: signing up and checking a username. Both are public."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get_throttles(self) -> list[BaseThrottle]:
        throttles = ACTION_THROTTLES.get(self.action or '')
        if throttles is None:
            return super().get_throttles()
        return [throttle() for throttle in throttles]

    @account_create_schema
    def create(self, request: Request) -> SuccessResponse:
        serializer = AccountCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        values.pop('policies_accepted')  # accepted by signing up (R6)
        registered = AccountRegistrationService().register(account=NewAccount(**values))
        return SuccessResponse(
            AccountCreateOutputSerializer(registered).data, status=HTTPStatus.CREATED
        )

    @username_availability_schema
    @action(detail=False, methods=['get'], url_path='username-availability')
    def username_availability(self, request: Request) -> SuccessResponse:
        serializer = UsernameAvailabilityInputSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        available = username_is_available(
            username=serializer.validated_data['username']
        )
        return SuccessResponse(
            UsernameAvailabilityOutputSerializer({'available': available}).data
        )
