#!/usr/bin/env python
import os
import sys
import django

# Django'ну жүктөө
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from core.models import Student, UserProfile
from django.contrib.auth.models import User

# ID 66дагы студентти табуу  
student_66 = Student.objects.get(id=66)
print(f'Студент ID 66: {student_66.name}, User: {student_66.user}')

# Жаңы уникалдуу User түзүү
username = 'student.aigerim'
counter = 1
base_username = username
while User.objects.filter(username=username).exists():
    username = f'{base_username}{counter}'
    counter += 1

print(f'Жаңы username: {username}')

# User түзүү
user = User.objects.create_user(
    username=username,
    first_name='Айгерим',
    last_name='Турдубекова',
    email=f'{username}@salymbekov.kg',
    password='student123'
)
print('✓ User түзүлдү')

# UserProfile түзүү
profile, created = UserProfile.objects.get_or_create(
    user=user,
    defaults={'role': 'STUDENT'}
)
if created:
    print('✓ UserProfile түзүлдү')
else:
    print('UserProfile эчак бар болчу')

# Студентти байланыштыруу
student_66.user = user
student_66.save()
print('✓ Студент байланыштырылды')

print(f'\nПРОВЕРКА: {student_66.name} -> {student_66.user.username}')

# Финалдык статистика
final_count = Student.objects.filter(user__isnull=True).count()
total_students = Student.objects.count()
print(f'\nНАТЫЙЖА:')
print(f'User аккаунту жок калган студенттер: {final_count}')
print(f'Жалпы студенттер: {total_students}')
print(f'User аккаунту бар студенттер: {total_students - final_count}')