from django.db import models


class Subject(models.Model):
    subject_code = models.CharField(
        max_length=20,
        unique=True
    )

    subject_name = models.CharField(
        max_length=100
    )

    max_marks = models.PositiveIntegerField(default=100)

    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.subject_code} - {self.subject_name}"