from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):

    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('ADMIN', 'Admin'),  # backwards compatibility
        ('STAFF', 'Staff'),
        ('STUDENT', 'Student'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='userprofile'
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='STUDENT'
    )

    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    @property
    def is_super_admin(self):
        return self.role in ['SUPER_ADMIN', 'ADMIN'] or self.user.is_superuser

    @property
    def is_staff_member(self):
        return self.role == 'STAFF'

    @property
    def is_student(self):
        return self.role == 'STUDENT'


class StaffProfile(models.Model):
    user_profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='staff_details'
    )
    staff_id = models.CharField(max_length=30, unique=True, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.user_profile.user.get_full_name() or self.user_profile.user.username} ({self.staff_id or 'Staff'})"
