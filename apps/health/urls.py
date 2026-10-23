from django.urls import path

from apps.health.apis import HealthViewSet

urlpatterns = [path('health/', HealthViewSet.as_view({'get': 'check'}), name='health')]
