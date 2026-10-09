from django.urls import path

from apps.core.services.health_check_service import HealthCheckService
from apps.core.utilities.dependencies_check import DependenciesCheck
from apps.core.views import HealthCheckView

urlpatterns = [
    path(
        'health/',
        HealthCheckView.as_view(
            health_check_service=HealthCheckService(DependenciesCheck())
        ),
        name='health',
    ),
]
