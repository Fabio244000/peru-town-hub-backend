import pytest
from django.urls import reverse

from tests.factories.accounts import TEST_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db


def test_staff_signs_in_to_the_admin_with_email_and_password(client):
    user = UserFactory(is_staff=True)

    response = client.post(
        reverse('admin:login'),
        {'username': user.email, 'password': TEST_PASSWORD},
    )

    assert response.status_code == 302
    assert client.get(reverse('admin:index')).status_code == 200
