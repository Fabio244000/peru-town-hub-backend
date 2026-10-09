from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.services.health_check_service import HealthCheckService


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    health_check_service: HealthCheckService = None

    def get(self, request):
        health_status = self.health_check_service.get_health_status()

        return Response(
            {'status': health_status.status, 'detail': health_status.detail},
            status=(
                status.HTTP_200_OK
                if health_status.is_healthy
                else status.HTTP_503_SERVICE_UNAVAILABLE
            ),
        )
