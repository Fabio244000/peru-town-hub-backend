from django.db import models
from django.utils import timezone


class BaseModel(models.Model):
    # No auto_now: services set both from their single clock reading.
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True
