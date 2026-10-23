from http import HTTPStatus

import pytest
from django.db import OperationalError
from django.db.backends.base.base import BaseDatabaseWrapper
from django.urls import reverse
from rest_framework.test import APIClient

from apps.health.constants import (
    DATABASE_DEPENDENCY,
    DATABASE_INTEGRATION_ERROR,
    DEPENDENCY_ERROR,
    DEPENDENCY_OK,
    HEALTH_OK_MESSAGE,
)


@pytest.mark.django_db
def test_health_reports_ok_when_the_system_is_healthy():
    response = APIClient().get(reverse('health'))

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        'success': True,
        'message': HEALTH_OK_MESSAGE,
        'data': {DATABASE_DEPENDENCY: DEPENDENCY_OK},
        'detail': None,
    }


def test_health_reports_which_dependency_failed(monkeypatch):
    def fail_to_connect(self):
        raise OperationalError('connection refused')

    monkeypatch.setattr(BaseDatabaseWrapper, 'ensure_connection', fail_to_connect)

    response = APIClient().get(reverse('health'))

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json() == {
        'success': False,
        'message': DATABASE_INTEGRATION_ERROR,
        'data': None,
        'detail': {DATABASE_DEPENDENCY: DEPENDENCY_ERROR},
    }


def test_api_schema_is_generated():
    response = APIClient().get(reverse('schema'))

    assert response.status_code == HTTPStatus.OK
