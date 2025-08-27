# attendance_system/attendance/models.py
from django.db import models
from accounts.models import CustomUser
from schedule.models import Schedule

class TeacherAssignment(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['teacher', 'schedule']

class AttendanceRecord(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    is_present = models.BooleanField(default=False)
    date = models.DateField(auto_now_add=True)