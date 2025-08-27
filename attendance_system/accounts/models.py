from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
        ('manager', 'Manager'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)

    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="customuser_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="customuser_set",
        related_query_name="user",
    )

class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    parent = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='children', limit_choices_to={'role': 'parent'})
    teacher = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='students', limit_choices_to={'role': 'teacher'})
    group = models.ForeignKey('schedule.Group', on_delete=models.SET_NULL, null=True, related_name='students')  # Added for group assignment

class TeacherProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='teacher_profile')

class ParentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='parent_profile')

class ManagerProfile(models.Model):  # Added
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='manager_profile')