from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile, Student
from core.models import Course, Group, Teacher

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, role='STUDENT')

@receiver(post_save, sender=UserProfile)
def create_student_or_teacher(sender, instance, created, **kwargs):
    if created and instance.role == 'STUDENT':
        default_course = Course.objects.first()
        default_group = Group.objects.first()
        Student.objects.create(
            user=instance.user,
            name=instance.user.get_full_name() or instance.user.username,
            course=default_course,
            group=default_group
        )
    elif created and instance.role == 'TEACHER':
        Teacher.objects.create(
            user=instance.user,
            name=instance.user.get_full_name() or instance.user.username
        )