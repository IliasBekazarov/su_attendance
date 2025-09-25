# 🔧 КОД САПАТЫ ЖАКШЫРТУУ

## 1. Model Improvements

### 1.1 Базовый Abstract Model
```python
# core/models.py
from django.db import models
from django.utils import timezone
import uuid

class BaseModel(models.Model):
    """Бардык модулдар үчүн базовый класс"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True

# Бардык моделдерди BaseModel'ден мураскорлоо
class Student(BaseModel):
    name = models.CharField(max_length=200)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # ... башка fields
```

### 1.2 Manager жана QuerySet жакшыртуу
```python
# core/managers.py
from django.db import models
from django.utils import timezone
from datetime import date, timedelta

class ActiveManager(models.Manager):
    """Активдүү объектторду гана кайтаруучу manager"""
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class AttendanceQuerySet(models.QuerySet):
    """Катышуу үчүн custom QuerySet"""
    
    def for_date_range(self, start_date, end_date):
        return self.filter(date__range=[start_date, end_date])
    
    def for_current_week(self):
        today = date.today()
        start_week = today - timedelta(days=today.weekday())
        end_week = start_week + timedelta(days=6)
        return self.for_date_range(start_week, end_week)
    
    def for_student(self, student):
        return self.filter(student=student)
    
    def present_only(self):
        return self.filter(status='Present')
    
    def absent_only(self):
        return self.filter(status='Absent')
    
    def get_statistics(self):
        """Статистика кайтаруу"""
        return self.aggregate(
            total=models.Count('id'),
            present=models.Count('id', filter=models.Q(status='Present')),
            absent=models.Count('id', filter=models.Q(status='Absent')),
            late=models.Count('id', filter=models.Q(status='Late')),
            excused=models.Count('id', filter=models.Q(status='Excused')),
        )

class AttendanceManager(models.Manager):
    def get_queryset(self):
        return AttendanceQuerySet(self.model, using=self._db)
    
    def for_current_week(self):
        return self.get_queryset().for_current_week()
    
    def for_student(self, student):
        return self.get_queryset().for_student(student)

# Models'те колдонуу
class Attendance(BaseModel):
    # ... fields
    
    objects = AttendanceManager()
    active_objects = ActiveManager()
```

### 1.3 Model Methods жакшыртуу
```python
# core/models.py
class Student(BaseModel):
    # ... fields
    
    class Meta:
        db_table = 'core_students'
        indexes = [
            models.Index(fields=['group', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]
        
    def __str__(self):
        return f"{self.name} ({self.group.name if self.group else 'Группасы жок'})"
    
    @property
    def full_name(self):
        """Толук ат"""
        return f"{self.user.first_name} {self.user.last_name}".strip() or self.name
    
    def get_attendance_percentage(self, subject=None, date_from=None, date_to=None):
        """Катышуу пайызын эсептөө"""
        from django.db.models import Count, Q
        from datetime import date, timedelta
        
        if not date_from:
            date_from = date.today() - timedelta(days=30)  # Соңку 30 күн
        if not date_to:
            date_to = date.today()
        
        query = self.attendance_set.filter(
            date__range=[date_from, date_to],
            is_active=True
        )
        
        if subject:
            query = query.filter(subject=subject)
        
        stats = query.aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status='Present')),
        )
        
        if stats['total'] == 0:
            return 0.0
        
        return round((stats['present'] / stats['total']) * 100, 2)
    
    def get_current_week_attendance(self):
        """Ушул жуманын катышуусу"""
        return Attendance.objects.for_student(self).for_current_week()
    
    def has_attendance_today(self, subject):
        """Бүгүн бул предмет боюнча катышуу белгиленгенби"""
        return Attendance.objects.filter(
            student=self,
            subject=subject,
            date=date.today(),
            is_active=True
        ).exists()
```

## 2. API Improvements

### 2.1 Custom Pagination
```python
# core/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'page_size': self.page_size,
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'results': data
        })
```

### 2.2 Custom Exception Handler
```python
# core/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """Custom exception handler"""
    response = exception_handler(exc, context)
    
    if response is not None:
        custom_response_data = {
            'error': True,
            'message': 'An error occurred',
            'details': response.data,
            'status_code': response.status_code
        }
        
        # Логго жазуу
        logger.error(f"API Error: {exc} - Context: {context}")
        
        response.data = custom_response_data
    
    return response
```

### 2.3 Improved Serializers
```python
# core/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *

class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """Динамикалык fields менен serializer"""
    
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        exclude = kwargs.pop('exclude', None)
        
        super().__init__(*args, **kwargs)
        
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
        
        if exclude is not None:
            for field_name in exclude:
                self.fields.pop(field_name, None)

class StudentDetailSerializer(DynamicFieldsModelSerializer):
    """Студент детальной маалыматы"""
    attendance_percentage = serializers.SerializerMethodField()
    total_classes_this_month = serializers.SerializerMethodField()
    present_classes_this_month = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = '__all__'
    
    def get_attendance_percentage(self, obj):
        return obj.get_attendance_percentage()
    
    def get_total_classes_this_month(self, obj):
        from datetime import date, timedelta
        start_date = date.today().replace(day=1)
        return obj.attendance_set.filter(
            date__gte=start_date,
            is_active=True
        ).count()
    
    def get_present_classes_this_month(self, obj):
        from datetime import date, timedelta
        start_date = date.today().replace(day=1)
        return obj.attendance_set.filter(
            date__gte=start_date,
            status='Present',
            is_active=True
        ).count()

class AttendanceStatsSerializer(serializers.Serializer):
    """Катышуу статистикасы үчүн serializer"""
    total_classes = serializers.IntegerField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    late_count = serializers.IntegerField()
    excused_count = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()
    date_from = serializers.DateField()
    date_to = serializers.DateField()
```

## 3. Testing Strategy

### 3.1 Model Tests
```python
# core/tests/test_models.py
from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Student, Teacher, Course, Group, Subject, Attendance
from datetime import date, timedelta

class StudentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test_student',
            email='student@test.com',
            password='testpass123'
        )
        self.course = Course.objects.create(name='Computer Science', year=1)
        self.group = Group.objects.create(name='CS-101', course=self.course)
        self.student = Student.objects.create(
            name='Test Student',
            user=self.user,
            group=self.group
        )
    
    def test_student_creation(self):
        """Студент туура түзүлөрүн текшерүү"""
        self.assertTrue(isinstance(self.student, Student))
        self.assertEqual(self.student.__str__(), "Test Student (CS-101)")
    
    def test_attendance_percentage_calculation(self):
        """Катышуу пайызын туура эсептөөрүн текшерүү"""
        # Test data түзүү
        teacher_user = User.objects.create_user('teacher', 'teacher@test.com', 'pass')
        teacher = Teacher.objects.create(name='Test Teacher', user=teacher_user)
        subject = Subject.objects.create(name='Math', teacher=teacher)
        
        # 5 күн катышуу: 4 Present, 1 Absent
        for i in range(5):
            status = 'Present' if i < 4 else 'Absent'
            Attendance.objects.create(
                student=self.student,
                subject=subject,
                date=date.today() - timedelta(days=i),
                status=status
            )
        
        percentage = self.student.get_attendance_percentage()
        self.assertEqual(percentage, 80.0)  # 4/5 * 100 = 80%
```

### 3.2 API Tests
```python
# core/tests/test_api.py
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from core.models import *

class AttendanceAPITest(APITestCase):
    def setUp(self):
        # Test data
        self.teacher_user = User.objects.create_user('teacher', 'teacher@test.com', 'pass')
        self.student_user = User.objects.create_user('student', 'student@test.com', 'pass')
        
        # Create profiles
        UserProfile.objects.create(user=self.teacher_user, role='TEACHER')
        UserProfile.objects.create(user=self.student_user, role='STUDENT')
        
        # Create related objects
        self.course = Course.objects.create(name='CS', year=1)
        self.group = Group.objects.create(name='CS-101', course=self.course)
        self.teacher = Teacher.objects.create(name='Teacher', user=self.teacher_user)
        self.student = Student.objects.create(name='Student', user=self.student_user, group=self.group)
        self.subject = Subject.objects.create(name='Math', teacher=self.teacher)
    
    def test_mark_attendance_api(self):
        """Катышуу белгилөө API тести"""
        self.client.force_authenticate(user=self.teacher_user)
        
        data = {
            'student': self.student.id,
            'subject': self.subject.id,
            'date': date.today().strftime('%Y-%m-%d'),
            'status': 'Present'
        }
        
        response = self.client.post('/api/attendance/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Маалымат базасында сакталганын текшерүү
        attendance = Attendance.objects.get(
            student=self.student,
            subject=self.subject,
            date=date.today()
        )
        self.assertEqual(attendance.status, 'Present')
```

## 4. Performance Optimization

### 4.1 Database Query Optimization
```python
# core/views.py
from django.db.models import Prefetch, Count, Q

class OptimizedStudentViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        """Оптимизацияланган queryset"""
        return Student.objects.select_related(
            'user',
            'group',
            'group__course'
        ).prefetch_related(
            Prefetch(
                'attendance_set',
                queryset=Attendance.objects.select_related('subject')
                .filter(date__gte=date.today() - timedelta(days=30))
            )
        ).annotate(
            attendance_count=Count('attendance'),
            present_count=Count('attendance', filter=Q(attendance__status='Present'))
        )
```

### 4.2 Caching Strategy
```python
# core/utils.py
from django.core.cache import cache
from django.conf import settings
import hashlib

def get_cache_key(prefix, *args):
    """Cache key генерация кылуу"""
    key_data = f"{prefix}:{'_'.join(map(str, args))}"
    return hashlib.md5(key_data.encode()).hexdigest()

def cached_attendance_stats(student_id, subject_id=None, days=30):
    """Кэшталган катышуу статистикасы"""
    cache_key = get_cache_key('attendance_stats', student_id, subject_id, days)
    
    stats = cache.get(cache_key)
    if stats is None:
        student = Student.objects.get(id=student_id)
        stats = student.get_attendance_percentage(
            subject_id=subject_id,
            date_from=date.today() - timedelta(days=days)
        )
        cache.set(cache_key, stats, timeout=3600)  # 1 саат кэш
    
    return stats
```

## 5. Logging жана Monitoring

### 5.1 Logging Configuration
```python
# attendance_system/settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/attendance.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'core': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 5.2 Monitoring Decorators
```python
# core/decorators.py
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)

def log_execution_time(func):
    """Функциянын аткарылуу убакытын логдоо"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger.info(f"{func.__name__} executed in {end_time - start_time:.2f} seconds")
        return result
    return wrapper

def log_api_access(func):
    """API access логдоо"""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        user = getattr(request, 'user', None)
        user_info = user.username if user and user.is_authenticated else 'Anonymous'
        
        logger.info(f"API Access: {func.__name__} by {user_info}")
        return func(request, *args, **kwargs)
    return wrapper
```