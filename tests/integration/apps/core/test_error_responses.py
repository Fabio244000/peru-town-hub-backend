from http import HTTPStatus

from django.urls import reverse
from rest_framework import exceptions
from rest_framework.test import APIClient

from apps.core.constants import NOT_FOUND_MESSAGE


def test_drf_errors_are_returned_with_the_envelope():
    response = APIClient().post(reverse('health'))

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert response.json() == {
        'success': False,
        'message': str(exceptions.MethodNotAllowed('POST').detail),
        'data': None,
        'detail': None,
    }


def test_unknown_url_returns_json_not_found_envelope():
    response = APIClient().get('/not-exist/')

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        'success': False,
        'message': NOT_FOUND_MESSAGE,
        'data': None,
        'detail': None,
    }
