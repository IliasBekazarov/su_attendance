#!/usr/bin/env python3
"""
Жаңы курс/группа структурасын түзүү
1-курс: CS-11, CS-12, CS-13, CS-14, CS-15
2-курс: CS-21, CS-22, CS-23, CS-24, CS-25
3-курс: CS-31, CS-32, CS-33, CS-34, CS-35
"""
import os
import sys
import django
from datetime import time

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import (
    UserProfile, Student, Teacher, Course, Group, 
    Subject, Schedule, Attendance
)

def create_new_structure():
    """Жаңы курс-группа структурасын түзүү"""
    
    print("🏗️ Жаңы курс/группа структурасын түзүү...")
    
    # Эски маалыматтарды тазалоо
    print("🧹 Эски маалыматтарды тазалоо...")
    Schedule.objects.all().delete()
    Attendance.objects.all().delete()
    Student.objects.all().delete()
    Subject.objects.all().delete()
    Group.objects.all().delete()
    Course.objects.all().delete()
    
    # Жаңы курстарды түзүү
    print("📚 Курстарды түзүү...")
    course1 = Course.objects.create(name="1-курс", year=1)
    course2 = Course.objects.create(name="2-курс", year=2)
    course3 = Course.objects.create(name="3-курс", year=3)
    
    # Ар курс үчүн 5 группадан түзүү
    print("👥 Группаларды түзүү...")
    groups = {}
    
    # 1-курс группалары
    for i in range(1, 6):
        group_name = f"CS-1{i}"
        groups[group_name] = Group.objects.create(name=group_name, course=course1)
    
    # 2-курс группалары
    for i in range(1, 6):
        group_name = f"CS-2{i}"
        groups[group_name] = Group.objects.create(name=group_name, course=course2)
    
    # 3-курс группалары
    for i in range(1, 6):
        group_name = f"CS-3{i}"
        groups[group_name] = Group.objects.create(name=group_name, course=course3)
    
    # Мугалимдерди алуу (мурдагы маалыматтардан)
    teachers = Teacher.objects.all()
    if not teachers:
        print("❌ Мугалимдер табылган жок! Алгач мугалимдерди түзүңүз.")
        return
    
    print(f"👨‍🏫 {teachers.count()} мугалим табылды")
    
    # Предметтерди түзүү (курс боюнча)
    print("📖 Предметтерди түзүү...")
    subjects = []
    
    # 1-курс предметтери
    subjects.extend([
        Subject.objects.create(subject_name="Python Программалоо Негиздери", teacher=teachers[0], course=course1),
        Subject.objects.create(subject_name="Математика 1", teacher=teachers[1], course=course1),
        Subject.objects.create(subject_name="Англис тили", teacher=teachers[2], course=course1),
    ])
    
    # 2-курс предметтери
    subjects.extend([
        Subject.objects.create(subject_name="Веб Программалоо", teacher=teachers[0], course=course2),
        Subject.objects.create(subject_name="Маалымат Базалары", teacher=teachers[1], course=course2),
        Subject.objects.create(subject_name="Алгоритмдер жана Маалымат Түзүмдөрү", teacher=teachers[2], course=course2),
    ])
    
    # 3-курс предметтери
    subjects.extend([
        Subject.objects.create(subject_name="Программалык Инженерия", teacher=teachers[0], course=course3),
        Subject.objects.create(subject_name="Компьютердик Желелер", teacher=teachers[1], course=course3),
        Subject.objects.create(subject_name="Мобилдик Программалоо", teacher=teachers[2], course=course3),
    ])
    
    # Студенттерди түзүү
    print("🎓 Студенттерди түзүү...")
    student_users = User.objects.filter(userprofile__role='STUDENT')
    
    if not student_users:
        print("❌ Студент колдонуучулар табылган жок!")
        return
    
    # Студенттерди группаларга бөлүү
    group_list = list(groups.values())
    students_per_group = len(student_users) // len(group_list) + 1
    
    for i, user in enumerate(student_users):
        group_index = i // students_per_group
        if group_index >= len(group_list):
            group_index = len(group_list) - 1
        
        group = group_list[group_index]
        
        Student.objects.create(
            name=f"{user.first_name} {user.last_name}" if user.first_name else user.username,
            user=user,
            course=group.course,
            group=group
        )
    
    # Расписание түзүү (жеңилдетилген)
    print("📅 Расписаниени түзүү...")
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    time_slots = [
        (time(9, 0), time(10, 30)),   # 1-пара
        (time(10, 45), time(12, 15)), # 2-пара  
        (time(13, 0), time(14, 30)),  # 3-пара
        (time(14, 45), time(16, 15)), # 4-пара
    ]
    
    # Ар группа үчүн жөнөкөй расписание
    for group in groups.values():
        course_subjects = Subject.objects.filter(course=group.course)
        if course_subjects:
            for day_idx, day in enumerate(days):
                if day_idx < len(course_subjects):
                    subject = course_subjects[day_idx % len(course_subjects)]
                    slot = time_slots[day_idx % len(time_slots)]
                    
                    Schedule.objects.create(
                        subject=subject,
                        group=group,
                        day=day,
                        start_time=slot[0],
                        end_time=slot[1]
                    )
    
    print("\n✅ Жаңы структура ийгиликтүү түзүлдү!")
    print(f"📊 Статистика:")
    print(f"   Курстар: {Course.objects.count()}")
    print(f"   Группалар: {Group.objects.count()}")
    print(f"   Предметтер: {Subject.objects.count()}")
    print(f"   Студенттер: {Student.objects.count()}")
    print(f"   Расписание: {Schedule.objects.count()}")

if __name__ == '__main__':
    try:
        create_new_structure()
    except Exception as e:
        print(f"❌ Ката чыкты: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
