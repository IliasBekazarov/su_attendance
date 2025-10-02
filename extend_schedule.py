#!/usr/bin/env python3
"""
5-6 күндүк толук расписаниени түзүү
"""
import os
import sys
import django
from datetime import time

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
django.setup()

from core.models import Schedule, Subject, Group

def create_full_schedule():
    """Толук жумалык расписаниени түзүү"""
    
    print("📅 5-6 күндүк толук расписаниени түзүү...")
    
    # Учурдагы расписаниени өчүрүү
    Schedule.objects.all().delete()
    
    # Предметтер жана группалар
    subjects = Subject.objects.all()
    groups = Group.objects.all()
    
    if not subjects.exists() or not groups.exists():
        print("❌ Алгач сабактар жана группалар түзүлүшү керек!")
        return
    
    # Убакыт слоттары
    time_slots = [
        (time(8, 30), time(10, 0)),   # 1-пара
        (time(10, 15), time(11, 45)), # 2-пара  
        (time(12, 0), time(13, 30)),  # 3-пара
        (time(14, 30), time(16, 0)),  # 4-пара
        (time(16, 15), time(17, 45)), # 5-пара
    ]
    
    # Күндөр
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    # Ар бир группа үчүн расписание
    schedule_data = []
    
    # КИ-21 группасы (биринчи табылганын алабыз)
    ki21 = Group.objects.filter(name="КИ-21").first()
    python_subj = Subject.objects.get(subject_name="Python Программалоо")
    web_subj = Subject.objects.get(subject_name="Веб Өндүрүү") 
    db_subj = Subject.objects.get(subject_name="Маалымат Базалары")
    
    ki21_schedule = [
        # Дүйшөмбү
        ('Monday', 0, python_subj),
        ('Monday', 1, web_subj),
        ('Monday', 2, db_subj),
        # Шейшемби
        ('Tuesday', 0, web_subj),
        ('Tuesday', 1, python_subj),
        ('Tuesday', 3, db_subj),
        # Шаршемби
        ('Wednesday', 1, python_subj),
        ('Wednesday', 2, web_subj),
        ('Wednesday', 3, db_subj),
        # Бейшемби
        ('Thursday', 0, db_subj),
        ('Thursday', 1, python_subj),
        ('Thursday', 2, web_subj),
        # Жума
        ('Friday', 0, python_subj),
        ('Friday', 1, db_subj),
        # Ишемби
        ('Saturday', 0, web_subj),
    ]
    
    for day, slot_idx, subject in ki21_schedule:
        start_time, end_time = time_slots[slot_idx]
        Schedule.objects.create(
            subject=subject,
            group=ki21,
            day=day,
            start_time=start_time,
            end_time=end_time
        )
    
    # КИ-22 группасы
    ki22 = Group.objects.filter(name="КИ-22").first()
    ki22_schedule = [
        # Дүйшөмбү
        ('Monday', 1, python_subj),
        ('Monday', 2, web_subj),
        ('Monday', 3, db_subj),
        # Шейшемби
        ('Tuesday', 0, db_subj),
        ('Tuesday', 2, python_subj),
        ('Tuesday', 3, web_subj),
        # Шаршемби
        ('Wednesday', 0, web_subj),
        ('Wednesday', 1, db_subj),
        ('Wednesday', 3, python_subj),
        # Бейшемби
        ('Thursday', 1, web_subj),
        ('Thursday', 2, python_subj),
        ('Thursday', 4, db_subj),
        # Жума
        ('Friday', 1, python_subj),
        ('Friday', 2, web_subj),
        # Ишемби
        ('Saturday', 1, db_subj),
    ]
    
    for day, slot_idx, subject in ki22_schedule:
        start_time, end_time = time_slots[slot_idx]
        Schedule.objects.create(
            subject=subject,
            group=ki22,
            day=day,
            start_time=start_time,
            end_time=end_time
        )
    
    # БА-21 группасы
    ba21 = Group.objects.filter(name="БА-21").first()
    mgmt_subj = Subject.objects.get(subject_name="Менеджмент")
    
    ba21_schedule = [
        ('Monday', 0, mgmt_subj),
        ('Monday', 3, mgmt_subj),
        ('Tuesday', 1, mgmt_subj),
        ('Tuesday', 4, mgmt_subj),
        ('Wednesday', 0, mgmt_subj),
        ('Wednesday', 2, mgmt_subj),
        ('Thursday', 1, mgmt_subj),
        ('Thursday', 3, mgmt_subj),
        ('Friday', 0, mgmt_subj),
        ('Friday', 3, mgmt_subj),
        ('Saturday', 0, mgmt_subj),
    ]
    
    for day, slot_idx, subject in ba21_schedule:
        start_time, end_time = time_slots[slot_idx]
        Schedule.objects.create(
            subject=subject,
            group=ba21,
            day=day,
            start_time=start_time,
            end_time=end_time
        )
    
    # ЭМ-21 группасы
    em21 = Group.objects.filter(name="ЭМ-21").first()
    dipl_subj = Subject.objects.get(subject_name="Дипломатия")
    
    em21_schedule = [
        ('Monday', 1, dipl_subj),
        ('Monday', 4, dipl_subj),
        ('Tuesday', 0, dipl_subj),
        ('Tuesday', 3, dipl_subj),
        ('Wednesday', 1, dipl_subj),
        ('Wednesday', 4, dipl_subj),
        ('Thursday', 0, dipl_subj),
        ('Thursday', 2, dipl_subj),
        ('Friday', 1, dipl_subj),
        ('Friday', 4, dipl_subj),
        ('Saturday', 2, dipl_subj),
    ]
    
    for day, slot_idx, subject in em21_schedule:
        start_time, end_time = time_slots[slot_idx]
        Schedule.objects.create(
            subject=subject,
            group=em21,
            day=day,
            start_time=start_time,
            end_time=end_time
        )
    
    print("✅ Толук жумалык расписание түзүлдү!")
    print(f"📊 Жалпысынан {Schedule.objects.count()} сабак расписанияда")

if __name__ == '__main__':
    try:
        create_full_schedule()
    except Exception as e:
        print(f"❌ Ката чыкты: {e}")
        sys.exit(1)
