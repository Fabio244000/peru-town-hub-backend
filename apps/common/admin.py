from django.contrib import admin
from django.forms import ModelForm
from django.http import HttpRequest
from django.utils import timezone

from apps.common.models import BaseModel


class BaseModelAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', 'updated_at')

    def save_model(
        self, request: HttpRequest, obj: BaseModel, form: ModelForm, change: bool
    ) -> None:
        obj.updated_at = timezone.now()
        super().save_model(request, obj, form, change)
