from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.request import Request

from apps.core.responses import SuccessResponse
from apps.health.apidocs.health import health_check_schema
from apps.health.constants import HEALTH_OK_MESSAGE
from apps.health.services import HealthCheckService


class HealthViewSet(viewsets.ViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]

    @health_check_schema
    def check(self, request: Request) -> SuccessResponse:
        statuses = HealthCheckService().check()
        return SuccessResponse(statuses, message=HEALTH_OK_MESSAGE)
