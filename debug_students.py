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

print('=== СТУДЕНТТЕРДИН АБАЛЫ ===')

# User аккаунту жок студенттер
students_without_user = Student.objects.filter(user__isnull=True)
print(f'User аккаунту жок студенттер саны: {students_without_user.count()}')

if students_without_user.exists():
    print('\nАлардын тизмеси:')
    for student in students_without_user:
        print(f'  - ID: {student.id}, Аты: {student.name}')

# Эч кимге байланышпаган User'лер
unused_users = User.objects.filter(student__isnull=True, teacher__isnull=True)
print(f'\nЭч кимге байланышпаган User лер саны: {unused_users.count()}')

if unused_users.exists() and unused_users.count() <= 10:
    print('\nАлардын тизмеси:')
    for user in unused_users:
        print(f'  - {user.username} ({user.first_name} {user.last_name})')

# Эгер эч кимге байланышпаган User'лер болсо, аларды студенттерге байланыштырабыз
if students_without_user.exists() and unused_users.exists():
    print('\n=== СТУДЕНТТЕРДИ USER МЕНЕН БАЙЛАНЫШТЫРУУ ===')
    
    students_list = list(students_without_user)
    users_list = list(unused_users)
    
    min_count = min(len(students_list), len(users_list))
    
    for i in range(min_count):
        student = students_list[i]
        user = users_list[i]
        
        # User маалыматтарын студенттин аты менен жаңылоо
        name_parts = student.name.strip().split()
        if len(name_parts) >= 2:
            user.first_name = name_parts[0]
            user.last_name = ' '.join(name_parts[1:])
        else:
            user.first_name = student.name
            user.last_name = ''
        
        user.save()
        
        # Студентти User менен байланыштыруу
        student.user = user
        student.save()
        
        print(f'✓ {student.name} -> {user.username}')
        
        # UserProfile түзүү эгерде жок болсо
        if not hasattr(user, 'userprofile'):
            profile = UserProfile.objects.create(
                user=user,
                role='STUDENT'
            )
            print(f'  + UserProfile түзүлдү')

print('\n=== ЖЫЙЫНТЫК ===')
remaining_students = Student.objects.filter(user__isnull=True).count()
print(f'User аккаунту жок калган студенттер: {remaining_students}')