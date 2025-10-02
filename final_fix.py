#!/usr/bin/env python
import os
import sys
import django

# Django'ну жүктөө
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from core.models import Student, UserProfile, Teacher
from django.contrib.auth.models import User

print('=== ЭРКИН USER ЛЕРДИ ТАБУУ ===')

# Эч кимге байланышпаган User лерди табуу
free_users = []
for user in User.objects.filter(id__gte=30):  # Жаңы түзүлгөн User'лер
    has_student = Student.objects.filter(user=user).exists()
    has_teacher = Teacher.objects.filter(user=user).exists()
    
    print(f'User {user.id} ({user.username}): студент={has_student}, мугалим={has_teacher}')
    
    if not has_student and not has_teacher:
        free_users.append(user)
        print(f'  -> ЭРКИН!')

print(f'\nЭркин User лер саны: {len(free_users)}')

if free_users:
    # ID 66 студентке эркин User дун биринин берүү
    student_66 = Student.objects.get(id=66)
    free_user = free_users[0]
    
    print(f'\nID 66 студент: {student_66.name}')
    print(f'Ага берилчү User: {free_user.username}')
    
    # User дин ат-жөнүн жаңылоо
    free_user.first_name = 'Айгерим'
    free_user.last_name = 'Турдубекова'
    free_user.save()
    
    # Студентке байлануу
    student_66.user = free_user
    student_66.save()
    
    print('✓ Ийгиликтүү байланыштырылды!')
    
    # UserProfile текшерүү
    profile, created = UserProfile.objects.get_or_create(
        user=free_user,
        defaults={'role': 'STUDENT'}
    )
    if created:
        print('✓ UserProfile түзүлдү')

# Финалдык текшерүү
remaining_count = Student.objects.filter(user__isnull=True).count()
print(f'\nUser аккаунту жок калган студенттер: {remaining_count}')

if remaining_count == 0:
    print('🎉 БАРДЫК СТУДЕНТТЕР USER МЕНЕН БАЙЛАНЫШТЫРЫЛДЫ!')