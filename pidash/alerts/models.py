"""Remembers what has already been reported, so one failure means one message."""

from django.db import models
from django.utils import timezone


class ServiceAlert(models.Model):
    service_id = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)
    raised_at = models.DateTimeField(default=timezone.now)
    notified = models.BooleanField(default=False)

    class Meta:
        ordering = ["service_id"]

    def __str__(self) -> str:
        return f"{self.service_id}: {self.label}"
