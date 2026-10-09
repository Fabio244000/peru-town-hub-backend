from rest_framework import status
from rest_framework.test import APIRequestFactory

from apps.core.constants import DATABASE_INTEGRATION_ERROR, HEALTH_STATUS_ERROR
from apps.core.services.health_check_service import HealthCheckService
from apps.core.views import HealthCheckView

HEALTH_URL = '/api/v1/health/'


def test_health_returns_503_when_a_dependency_fails(fake_dependencies_check):
    view = HealthCheckView.as_view(
        health_check_service=HealthCheckService(
            fake_dependencies_check(errors=[DATABASE_INTEGRATION_ERROR])
        )
    )

    response = view(APIRequestFactory().get(HEALTH_URL))

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.data == {
        'status': HEALTH_STATUS_ERROR,
        'detail': DATABASE_INTEGRATION_ERROR,
    }
