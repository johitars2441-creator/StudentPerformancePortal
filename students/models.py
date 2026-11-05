from django.db import models
from django.contrib.auth.models import User


class Student(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student'
    )

    roll_number = models.CharField(
        max_length=20,
        unique=True
    )

    full_name = models.CharField(max_length=100)

    email = models.EmailField(unique=True)

    department = models.CharField(max_length=100)

    admission_date = models.DateField()

    def __str__(self):
        return f"{self.roll_number} - {self.full_name}"