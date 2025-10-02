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
    
    GENDER_CHOICES = (
        ('M', 'Эркек'),
        ('F', 'Аял'),
        ('O', 'Башка'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')
    students = models.ManyToManyField('Student', blank=True, related_name='student_profiles')
    
    # Жеке маалыматтар
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True, verbose_name='Профил сүрөтү')
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='Телефон номери')
    birth_date = models.DateField(blank=True, null=True, verbose_name='Туулган күнү')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True, verbose_name='Жынысы')
    address = models.TextField(blank=True, null=True, verbose_name='Дареги')
    bio = models.TextField(blank=True, null=True, verbose_name='Өзү жөнүндө', help_text='Кыскача маалымат')
    
    # Байланыш маалыматтары
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Тез кырдаал учурундагы байланышуучу')
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='Тез кырдаал телефону')
    
    # Система маалыматтары
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    is_profile_complete = models.BooleanField(default=False, verbose_name='Профил толтурулганбы')

    def __str__(self):
        return self.user.username
    
    @property
    def full_name(self):
        """Толук аты"""
        return f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username
    
    @property
    def age(self):
        """Курагы"""
        if self.birth_date:
            from datetime import date
            today = date.today()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None
    
    def check_profile_completeness(self):
        """Профилдин толук экенин текшерүү"""
        required_fields = [
            self.user.first_name,
            self.user.last_name,
            self.user.email,
            self.phone_number,
        ]
        self.is_profile_complete = all(field for field in required_fields)
        self.save()
        return self.is_profile_complete
    
    class Meta:
        verbose_name = 'Колдонуучу профили'
        verbose_name_plural = 'Колдонуучулардын профилдери'

class Student(models.Model):
    name = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    course = models.ForeignKey('Course', on_delete=models.SET_NULL, null=True)
    group = models.ForeignKey('Group', on_delete=models.SET_NULL, null=True)
    parents = models.ManyToManyField(UserProfile, blank=True, related_name='parent_profiles')

    def __str__(self):
        return self.name

class Teacher(models.Model):
    DEGREE_CHOICES = [
        ('PROFESSOR', 'Профессор'),
        ('DOCENT', 'Доцент'),  
        ('LECTURER', 'Лектор'),
        ('ASSISTANT', 'Ассистент'),
        ('TEACHER', 'Мугалим'),
    ]
    
    name = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    degree = models.CharField(max_length=20, choices=DEGREE_CHOICES, default='TEACHER')
    department = models.CharField(max_length=100, blank=True, null=True)  # Кафедра

    def __str__(self):
        return f"{self.name} ({self.get_degree_display()})"

class Course(models.Model):
    name = models.CharField(max_length=100)
    year = models.IntegerField()
    faculty = models.CharField(max_length=100, blank=True, null=True)  # Факультет
    
    class Meta:
        ordering = ['year', 'name']

    def __str__(self):
        return f"{self.name} ({self.year}-курс)"

class Group(models.Model):
    name = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, default=1)
    capacity = models.IntegerField(default=25)  # Группадагы студенттердин саны
    
    class Meta:
        ordering = ['course__year', 'name']

    def __str__(self):
        return f"{self.name} ({self.course.name})"

class Subject(models.Model):
    subject_name = models.CharField(max_length=100)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, default=1)  # Дефолт маани катары Course ID 1

    def __str__(self):
        return self.subject_name

class TimeSlot(models.Model):
    """Убакыт слоттору (админ тарабынан конфигурацияланат)"""
    name = models.CharField(max_length=50, verbose_name="Период аты")  # "1-пара", "2-пара"
    start_time = models.TimeField(verbose_name="Башталуу убакыты")
    end_time = models.TimeField(verbose_name="Аяктоо убакыты")
    order = models.IntegerField(default=1, verbose_name="Тартиби")  # Тартипке салуу үчүн
    is_active = models.BooleanField(default=True, verbose_name="Активдүү")
    
    class Meta:
        ordering = ['order']
        verbose_name = 'Убакыт периоду'
        verbose_name_plural = 'Убакыт периоддору'
    
    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"
    
    def get_duration_minutes(self):
        """Период узундугу (мүнөттөрдө)"""
        from datetime import datetime, timedelta
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        if end < start:  # Эгер период түнкүдө болсо
            end += timedelta(days=1)
        return int((end - start).total_seconds() / 60)

class Schedule(models.Model):
    DAY_CHOICES = [
        ('Monday', 'Дүйшөмбү'),
        ('Tuesday', 'Шейшемби'),
        ('Wednesday', 'Шаршемби'),
        ('Thursday', 'Бейшемби'),
        ('Friday', 'Жума'),
        ('Saturday', 'Ишемби'),
        ('Sunday', 'Жекшемби'),  # Жекшемби кошулду
    ]
    
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Сабак")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name="Группа")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Мугалим")
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Убакыт периоду")
    day = models.CharField(max_length=10, choices=DAY_CHOICES, verbose_name="Күн")
    room = models.CharField(max_length=50, blank=True, null=True, verbose_name="Кабинет")
    
    # Кошумча маалыматтар
    is_active = models.BooleanField(default=True, verbose_name="Активдүү")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    class Meta:
        # unique_together өчүрүлдү, анткени биз is_active фильтрин колдонобуз
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписаниелер'
        ordering = ['day', 'time_slot__order']

    def __str__(self):
        teacher_name = self.teacher.name if self.teacher else self.subject.teacher.name if self.subject.teacher else "Мугалим жок"
        return f"{self.subject.subject_name} - {self.group.name} ({self.get_day_display()}, {teacher_name})"
    
    @property
    def start_time(self):
        """Backward compatibility"""
        return self.time_slot.start_time if self.time_slot else None
    
    @property 
    def end_time(self):
        """Backward compatibility"""
        return self.time_slot.end_time if self.time_slot else None

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Күтүүдө'),
        ('APPROVED', 'Бекитилген'),
        ('REJECTED', 'Четке кагылган'),
    ]
    
    LEAVE_TYPE_CHOICES = [
        ('SICK', 'Ооруу'),
        ('PERSONAL', 'Жеке иштер'),
        ('FAMILY', 'Үй-бүлөлүк иштер'),
        ('EMERGENCY', 'Тез кырдаал'),
        ('OTHER', 'Башка себептер'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES, default='SICK')
    start_date = models.DateField(verbose_name='Башталуу күнү')
    end_date = models.DateField(verbose_name='Аяктоо күнү')
    reason = models.TextField(verbose_name='Себеби')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Бошотуу сурамы'
        verbose_name_plural = 'Бошотуу сурамдары'
        
    def __str__(self):
        return f"{self.student.name} - {self.leave_type} ({self.start_date} - {self.end_date})"
    
    @property
    def duration(self):
        return (self.end_date - self.start_date).days + 1

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('Present', 'Катышты'),
        ('Absent', 'Катышкан жок'),
        ('Late', 'Кечикти'),
        ('Excused', 'Уруксат менен жок'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    marked_by_student = models.BooleanField(default=False, verbose_name='Студент тарабынан белгиленди')
    marked_at = models.DateTimeField(auto_now=True, verbose_name='Белгиленген убакыт')
    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.SET_NULL, null=True, blank=True, 
                                     verbose_name='Байланышкан бошотуу сурамы')

    def __str__(self):
        return f"{self.student.name} - {self.subject.subject_name} - {self.date}"
        
    class Meta:
        unique_together = ['student', 'subject', 'date']

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('ABSENCE', 'Жок болуу боюнча'),
        ('LEAVE_REQUEST', 'Бошотуу сурамы'),
        ('LEAVE_APPROVED', 'Бошотуу бекитилди'),
        ('LEAVE_REJECTED', 'Бошотуу четке кагылды'),
        ('GENERAL', 'Жалпы'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='GENERAL')
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    # Optional references
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.recipient.username}"