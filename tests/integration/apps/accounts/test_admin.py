import logging

import pytest
from django.urls import reverse

from tests.factories.accounts import TEST_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db


def test_staff_signs_in_to_the_admin_with_username_and_password(client):
    user = UserFactory(is_staff=True)

    response = client.post(
        reverse('admin:login'),
        {'username': user.username, 'password': TEST_PASSWORD},
    )

    assert response.status_code == 302
    assert client.get(reverse('admin:index')).status_code == 200


def test_a_failed_sign_in_to_the_admin_is_logged_without_who_tried(client, caplog):
    user = UserFactory(is_staff=True)

    with caplog.at_level(logging.WARNING):
        client.post(
            reverse('admin:login'),
            {'username': user.username, 'password': 'not-the-password'},
        )

    [record] = [
        r for r in caplog.records if getattr(r, 'event', None) == 'sign_in_failed'
    ]
    assert record.levelno == logging.WARNING
    assert user.username not in caplog.text
    assert 'not-the-password' not in caplog.text
