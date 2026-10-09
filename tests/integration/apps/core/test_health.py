import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.constants import HEALTH_DETAIL_OK, HEALTH_STATUS_OK

HEALTH_URL = '/api/health/'


@pytest.mark.django_db
def test_health_returns_ok_when_system_is_healthy():
    response = APIClient().get(HEALTH_URL)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'status': HEALTH_STATUS_OK, 'detail': HEALTH_DETAIL_OK}
