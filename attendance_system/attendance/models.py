from django.db import models
from accounts.models import CustomUser
from schedule.models import Schedule

class Timetable(models.Model):
    group = models.CharField(max_length=50)
    subject = models.CharField(max_length=100)
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return f"{self.subject} - {self.group}"

class TeacherAssignment(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['teacher', 'schedule']

class AttendanceRecord(models.Model):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, null=True, blank=True)  # Өзгөртүлдү
    is_present = models.BooleanField(default=False)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.date} - {'Present' if self.is_present else 'Absent'}"