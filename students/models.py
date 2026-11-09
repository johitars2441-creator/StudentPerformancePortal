from django.db import models
from django.contrib.auth.models import User
from batches.models import Batch


class Student(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student'
    )

    batch = models.ForeignKey(
        Batch,
        on_delete=models.PROTECT,
        related_name='students',
        null=True,
        blank=True
    )

    roll_number = models.CharField(
        max_length=20,
        unique=True
    )

    full_name = models.CharField(max_length=100)

    email = models.EmailField(unique=True)

    department = models.CharField(max_length=100)

    admission_date = models.DateField()

    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enrolled_students'
    )

    def __str__(self):
        batch_code = self.batch.batch_code if self.batch else "No Batch"
        return f"{self.roll_number} - {self.full_name} ({batch_code})"
