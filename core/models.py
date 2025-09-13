from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Админ'),
        ('MANAGER', 'Менеджер'),
        ('TEACHER', 'Мугалим'),
        ('STUDENT', 'Студент'),
        ('PARENT', 'Ата-энелер'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    students = models.ManyToManyField('Student', blank=True, related_name='student_profiles')

    def __str__(self):
        return self.user.username

class Student(models.Model):
    name = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    course = models.ForeignKey('Course', on_delete=models.SET_NULL, null=True)
    group = models.ForeignKey('Group', on_delete=models.SET_NULL, null=True)
    parents = models.ManyToManyField(UserProfile, blank=True, related_name='parent_profiles')

    def __str__(self):
        return self.name

class Teacher(models.Model):
    name = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    name = models.CharField(max_length=100)
    year = models.IntegerField()

    def __str__(self):
        return self.name

class Group(models.Model):
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, default=1)  # Дефолт маани катары Course ID 1

    def __str__(self):
        return self.name

class Subject(models.Model):
    subject_name = models.CharField(max_length=100)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, default=1)  # Дефолт маани катары Course ID 1

    def __str__(self):
        return self.subject_name

class Schedule(models.Model):
    DAY_CHOICES = [
        ('Monday', 'Дүйшөмбү'),
        ('Tuesday', 'Шейшемби'),
        ('Wednesday', 'Шаршемби'),
        ('Thursday', 'Бейшемби'),
        ('Friday', 'Жума'),
        ('Saturday', 'Ишемби'),
    ]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    day = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.subject.subject_name} - {self.group.name} ({self.day})"

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('Present', 'Катышты'),
        ('Absent', 'Катышкан жок'),
        ('Late', 'Кечикти'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.student.name} - {self.subject.subject_name} - {self.date}"

class Notification(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.teacher.name} -> {self.student.name}"