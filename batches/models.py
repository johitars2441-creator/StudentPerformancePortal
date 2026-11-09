from django.db import models
from django.contrib.auth.models import User


class Batch(models.Model):
    batch_code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique identifier for the batch (e.g., BATCH-2026-PY01)"
    )
    batch_name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Batches"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.batch_code} - {self.batch_name}"


class BatchStaffAssignment(models.Model):
    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name='staff_assignments'
    )
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_batches'
    )
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_assignments_given'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('batch', 'staff')

    def __str__(self):
        return f"{self.staff.username} -> {self.batch.batch_code}"
