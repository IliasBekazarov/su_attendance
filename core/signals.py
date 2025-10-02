from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile, Student, Course, Group, Teacher, Attendance, Notification, Subject

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Жаңы колдонуучу катталганда автоматтык түрдө профил түзүү"""
    if created:
        profile = UserProfile.objects.create(user=instance, role='STUDENT')
        # Профилдин толуктугун текшерүү
        profile.check_profile_completeness()

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """User сакталганда профилди да сактоо"""
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        # Эгер профил жок болсо, жаңысын түзүү
        UserProfile.objects.create(user=instance, role='STUDENT')

@receiver(post_save, sender=UserProfile)
def create_student_or_teacher(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'STUDENT':
            default_course = Course.objects.first() or Course.objects.create(name='1st Year', year=1)
            default_group = Group.objects.first() or Group.objects.create(name='A-Group', course=default_course)
            Student.objects.create(
                user=instance.user,
                name=instance.user.get_full_name() or instance.user.username,
                course=default_course,
                group=default_group
            )
        elif instance.role == 'TEACHER':
            Teacher.objects.create(
                user=instance.user,
                name=instance.user.get_full_name() or instance.user.username
            )
            
@receiver(post_save, sender=Attendance)
def create_absent_notification(sender, instance, created, **kwargs):
    if created and instance.status == 'Absent':
        teacher = instance.subject.teacher
        if teacher and teacher.user:
            Notification.objects.create(
                recipient=teacher.user,
                notification_type='ABSENCE',
                title='Студент катышкан жок',
                message=f"{instance.student.name} {instance.subject.subject_name} сабагына катышкан жок ({instance.date}).",
                student=instance.student
            )