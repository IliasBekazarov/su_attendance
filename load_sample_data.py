#!/usr/bin/env python3
"""
Катышуу системасына базалык маалыматтарды жүктөө
"""
import os
import sys
import django
from datetime import date, time

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import (
    UserProfile, Student, Teacher, Course, Group, 
    Subject, Schedule, Attendance, LeaveRequest
)

def create_sample_data():
    """Демо маалыматтарды түзүү"""
    
    print("🚀 Салымбеков Университетинин Катышуу Системасына демо маалыматтарды жүктөө...")
    
    # 1. Курстарды түзүү
    print("📚 Курстарды түзүү...")
    course1 = Course.objects.create(name="Компьютердик Илимдер", year=2024)
    course2 = Course.objects.create(name="Бизнес Администрациясы", year=2024)
    course3 = Course.objects.create(name="Эл аралык Мамилелер", year=2024)
    
    # 2. Группаларды түзүү  
    print("👥 Группаларды түзүү...")
    group1 = Group.objects.create(name="КИ-21", course=course1)
    group2 = Group.objects.create(name="КИ-22", course=course1)
    group3 = Group.objects.create(name="БА-21", course=course2)
    group4 = Group.objects.create(name="ЭМ-21", course=course3)
    
    # 3. Мугалимдерди түзүү
    print("👨‍🏫 Мугалимдерди түзүү...")
    
    # Мугалим колдонуучуларды түзүү
    teacher_user1, created = User.objects.get_or_create(
        username='teacher1',
        defaults={'email': 'teacher1@salymbekov.kg'})
    if created:
        teacher_user1.set_password('password123')
        teacher_user1.save()
        
    teacher_user2, created = User.objects.get_or_create(
        username='teacher2',
        defaults={'email': 'teacher2@salymbekov.kg'})
    if created:
        teacher_user2.set_password('password123')
        teacher_user2.save()
        
    teacher_user3, created = User.objects.get_or_create(
        username='teacher3', 
        defaults={'email': 'teacher3@salymbekov.kg'})
    if created:
        teacher_user3.set_password('password123')
        teacher_user3.save()
    
    # Teacher моделдерин түзүү
    teacher1, created = Teacher.objects.get_or_create(
        user=teacher_user1,
        defaults={'name': "Айгүл Бектурова"})
    teacher2, created = Teacher.objects.get_or_create(
        user=teacher_user2,
        defaults={'name': "Нурлан Сатыбалдиев"})
    teacher3, created = Teacher.objects.get_or_create(
        user=teacher_user3,
        defaults={'name': "Гүлзара Токтосунова"})
    
    # UserProfile түзүү
    UserProfile.objects.get_or_create(user=teacher_user1, defaults={'role': 'TEACHER'})
    UserProfile.objects.get_or_create(user=teacher_user2, defaults={'role': 'TEACHER'})  
    UserProfile.objects.get_or_create(user=teacher_user3, defaults={'role': 'TEACHER'})
    
    # 4. Сабактарды түзүү
    print("📖 Сабактарды түзүү...")
    subject1 = Subject.objects.create(subject_name="Python Программалоо", teacher=teacher1, course=course1)
    subject2 = Subject.objects.create(subject_name="Веб Өндүрүү", teacher=teacher1, course=course1)
    subject3 = Subject.objects.create(subject_name="Маалымат Базалары", teacher=teacher2, course=course1)
    subject4 = Subject.objects.create(subject_name="Менеджмент", teacher=teacher3, course=course2)
    subject5 = Subject.objects.create(subject_name="Дипломатия", teacher=teacher3, course=course3)
    
    # 5. Расписаниени түзүү
    print("📅 Расписаниени түзүү...")
    Schedule.objects.create(subject=subject1, group=group1, day='Monday', start_time=time(9, 0), end_time=time(10, 30))
    Schedule.objects.create(subject=subject2, group=group1, day='Tuesday', start_time=time(10, 40), end_time=time(12, 10))
    Schedule.objects.create(subject=subject3, group=group1, day='Wednesday', start_time=time(9, 0), end_time=time(10, 30))
    Schedule.objects.create(subject=subject1, group=group2, day='Monday', start_time=time(10, 40), end_time=time(12, 10))
    Schedule.objects.create(subject=subject4, group=group3, day='Thursday', start_time=time(9, 0), end_time=time(10, 30))
    Schedule.objects.create(subject=subject5, group=group4, day='Friday', start_time=time(10, 40), end_time=time(12, 10))
    
    # 6. Студенттерди түзүү
    print("🎓 Студенттерди түзүү...")
    
    # Студент колдонуучуларды түзүү
    student_users = []
    student_names = [
        "Алибек Жумабеков", "Айжан Токтосунова", "Бектур Асанов", 
        "Гүлнара Ирисбекова", "Данияр Маматов", "Жылдыз Орозова",
        "Кубанычбек Ниязов", "Мээрим Сатылганова", "Нурбек Токтогулов",
        "Перизат Касымбекова", "Темирлан Абдыракманов", "Чынара Жекшенова"
    ]
    
    for i, name in enumerate(student_names, 1):
        username = f"student{i}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': f'{username}@salymbekov.kg'}
        )
        if created:
            user.set_password('password123')
            user.save()
        student_users.append((user, name))
        UserProfile.objects.get_or_create(user=user, defaults={'role': 'STUDENT'})
    
    # Student моделдерин түзүү
    students = []
    group_assignment = [group1, group1, group1, group2, group2, group2, group3, group3, group3, group4, group4, group4]
    
    for i, (user, name) in enumerate(student_users):
        course = group_assignment[i].course
        student, created = Student.objects.get_or_create(
            user=user,
            defaults={
                'name': name, 
                'course': course, 
                'group': group_assignment[i]
            }
        )
        students.append(student)
    
    # 7. Ата-энелерди түзүү
    print("👨‍👩‍👧‍👦 Ата-энелерди түзүү...")
    parent_user1, created = User.objects.get_or_create(
        username='parent1',
        defaults={'email': 'parent1@example.com'}
    )
    if created:
        parent_user1.set_password('password123')
        parent_user1.save()
        
    parent_user2, created = User.objects.get_or_create(
        username='parent2', 
        defaults={'email': 'parent2@example.com'}
    )
    if created:
        parent_user2.set_password('password123')
        parent_user2.save()
    
    parent_profile1, created = UserProfile.objects.get_or_create(
        user=parent_user1, defaults={'role': 'PARENT'}
    )
    parent_profile2, created = UserProfile.objects.get_or_create(
        user=parent_user2, defaults={'role': 'PARENT'}
    )
    
    # Ата-энелерди балдарына байлоо
    parent_profile1.students.add(students[0], students[1])
    parent_profile2.students.add(students[2], students[3])
    
    # 8. Администраторду түзүү (эгерде жок болсо)
    admin_user, created = User.objects.get_or_create(username='admin')
    if created:
        admin_user.set_password('admin123')
        admin_user.is_superuser = True
        admin_user.is_staff = True
        admin_user.save()
    
    admin_profile, created = UserProfile.objects.get_or_create(
        user=admin_user,
        defaults={'role': 'ADMIN'}
    )
    
    # 9. Менеджерди түзүү
    manager_user, created = User.objects.get_or_create(
        username='manager1',
        defaults={'email': 'manager1@salymbekov.kg'}
    )
    if created:
        manager_user.set_password('password123')
        manager_user.save()
    UserProfile.objects.get_or_create(user=manager_user, defaults={'role': 'MANAGER'})
    
    print("\n✅ Базалык маалыматтар ийгиликтүү жүктөлдү!")
    print("\n🔑 Колдонуучулар:")
    print("   Админ: admin / admin123")
    print("   Менеджер: manager1 / password123")
    print("   Мугалим: teacher1, teacher2, teacher3 / password123")
    print("   Студенттер: student1, student2, ...student12 / password123")
    print("   Ата-энелер: parent1, parent2 / password123")
    print("\n🌐 Система: http://127.0.0.1:8001/")
    print("🔗 API: http://127.0.0.1:8001/api/v1/")
    print("⚙️  Админ: http://127.0.0.1:8001/admin/")

if __name__ == '__main__':
    try:
        create_sample_data()
    except Exception as e:
        print(f"❌ Ката чыкты: {e}")
        sys.exit(1)
