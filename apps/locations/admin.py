from django.contrib import admin

from apps.common.admin import BaseModelAdmin
from apps.locations.models import Department, District, PopulatedCenter, Province


@admin.register(Department, Province, District, PopulatedCenter)
class LocationAdmin(BaseModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')
    ordering = ('code',)
