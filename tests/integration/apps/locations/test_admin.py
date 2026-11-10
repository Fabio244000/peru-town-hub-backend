import pytest
from django.urls import reverse

from apps.locations.models import Department
from tests.factories.accounts import UserFactory
from tests.factories.locations import DepartmentFactory

pytestmark = pytest.mark.django_db


def test_an_edit_in_the_admin_saves_the_change_and_its_moment(client):
    client.force_login(UserFactory(is_staff=True, is_superuser=True))
    department = DepartmentFactory(code='050000', name='Ayacucho')

    client.post(
        reverse('admin:locations_department_change', args=[department.pk]),
        {'code': '050000', 'name': 'Ayacucho corregido'},
    )

    edited = Department.objects.get(pk=department.pk)
    assert edited.name == 'Ayacucho corregido'
    assert edited.updated_at > department.updated_at
