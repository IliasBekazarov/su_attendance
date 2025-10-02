"""
Жаңы Schedule систем view'лери
Талаптарга ылайык курс/группа фильтрациясы жана ролдор боюнч@login_required
def get_schedule_data(request):
    """
    AJAX API: Расписание маалыматтарын алуу
    Course жана Group фильтрлери менен
    """
    course_id = request.GET.get('course_id')
    group_id = request.GET.get('group_id')
    user_profile = request.user.userprofile
    
    print(f"DEBUG: get_schedule_data called - course_id: {course_id}, group_id: {group_id}, user_role: {user_profile.role}")
    
    # Уруксаттарды текшерүү
    if user_profile.role == 'STUDENT':
        try:
            student = Student.objects.get(user=request.user)
            print(f"DEBUG: Student found - group: {student.group.id if student.group else 'None'}")
            if group_id and str(student.group.id) != group_id:
                return JsonResponse({'error': 'Сизде бул группанын расписаниесин көрүү укугу жок'}, status=403)
        except Student.DoesNotExist:
            print(f"DEBUG: Student profile not found for user {request.user.username}")
            return JsonResponse({'error': 'Студент профили табылган жок'}, status=404)from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Prefetch
from django.utils.translation import gettext as _
from datetime import datetime, date, timedelta
import json

from .models import (
    UserProfile, Student, Teacher, Course, Group, Attendance, 
    Subject, Schedule, TimeSlot, Notification
)


@login_required
def unified_schedule(request):
    """
    Биргелешкен расписание системасы
    Ролдор боюнча ар кандай функциялар
    """
    user_profile = request.user.userprofile
    
    # Алгач колдонуучунун ролун аныктайбыз
    context = {
        'user_role': user_profile.role,
        'user_profile': user_profile,
    }
    
    # СТУДЕНТ үчүн - Өзүнүн группасын гана көрө алат
    if user_profile.role == 'STUDENT':
        try:
            student = Student.objects.get(user=request.user)
            if student.group:
                context.update({
                    'user_course': student.course,
                    'user_group': student.group,
                    'is_restricted_view': True,
                })
        except Student.DoesNotExist:
            messages.error(request, 'Студент профили табылган жок.')
            return redirect('dashboard')
    
    # АТА-ЭНЕ үчүн - Балдарынын группаларын көрө алат
    elif user_profile.role == 'PARENT':
        # Ата-энелер өз балдарынын группаларын көрө алат
        linked_students = user_profile.students.all()
        if linked_students.exists():
            context.update({
                'linked_students': linked_students,
                'is_restricted_view': True,
            })
        else:
            messages.warning(request, 'Сизге эч кандай студент байланышкан эмес.')
            return redirect('dashboard')
    
    # МУГАЛИМ/АДМИН/МЕНЕДЖЕР үчүн - Бардык расписаниени көрө алат
    else:
        context['is_restricted_view'] = False
        
        # Мугалим үчүн өзүнүн сабактарын белгилөө
        if user_profile.role == 'TEACHER':
            try:
                teacher = Teacher.objects.get(user=request.user)
                context['teacher_profile'] = teacher
            except Teacher.DoesNotExist:
                pass
    
    # Бардык курстар жана группалар (фильтрация үчүн)
    courses = Course.objects.all().order_by('year', 'name')
    groups = Group.objects.select_related('course').all().order_by('course__year', 'name')
    time_slots = TimeSlot.objects.filter(is_active=True).order_by('order')
    
    # Админ/Менеджер үчүн сабактар жана мугалимдер
    subjects = Subject.objects.select_related('teacher', 'course').all().order_by('subject_name')
    teachers = Teacher.objects.all().order_by('name')
    
    context.update({
        'courses': courses,
        'groups': groups, 
        'time_slots': time_slots,
        'subjects': subjects,
        'teachers': teachers,
        'days': Schedule.DAY_CHOICES,
    })
    
    return render(request, 'unified_schedule.html', context)


@login_required
def get_schedule_data(request):
    """
    AJAX аркылуу расписание маалыматтарын алуу
    Course жана Group фильтрлери менен
    """
    course_id = request.GET.get('course_id')
    group_id = request.GET.get('group_id')
    user_profile = request.user.userprofile
    
    # Уруксаттарды текшерүү
    if user_profile.role == 'STUDENT':
        try:
            student = Student.objects.get(user=request.user)
            if group_id and str(student.group.id) != group_id:
                return JsonResponse({'error': 'Сизде бул группанын расписаниесин көрүү укугу жок'}, status=403)
        except Student.DoesNotExist:
            return JsonResponse({'error': 'Студент профили табылган жок'}, status=404)
    
    elif user_profile.role == 'PARENT':
        # Ата-энелер балдарынын группаларын гана көрө алат
        linked_groups = [student.group.id for student in user_profile.students.all() if student.group]
        if group_id and int(group_id) not in linked_groups:
            return JsonResponse({'error': 'Сизде бул группанын расписаниесин көрүү укугу жок'}, status=403)
    
    # Фильтрлерди колдонуп расписаниени алуу
    schedules_query = Schedule.objects.select_related(
        'subject', 'teacher', 'group', 'time_slot'
    ).filter(is_active=True)
    
    if course_id:
        schedules_query = schedules_query.filter(group__course_id=course_id)
    
    if group_id:
        schedules_query = schedules_query.filter(group_id=group_id)
    
    schedules = schedules_query.order_by('day', 'time_slot__order')
    
    print(f"DEBUG: Found {schedules.count()} schedules for filters")
    
    # Маалыматтарды структуралашуу
    schedule_data = {}
    time_slots = TimeSlot.objects.filter(is_active=True).order_by('order')
    
    print(f"DEBUG: Found {time_slots.count()} active time slots")
    
    for schedule in schedules:
        # time_slot NULL болсо, бул schedule'ди өткөрүп кетебиз
        if not schedule.time_slot:
            print(f"DEBUG: Skipping schedule {schedule.id} - no time_slot")
            continue
            
        day = schedule.day
        time_slot_id = str(schedule.time_slot.id)
        
        if day not in schedule_data:
            schedule_data[day] = {}
        
        schedule_data[day][time_slot_id] = {
            'id': schedule.id,
            'subject': schedule.subject.subject_name,
            'teacher': schedule.teacher.name if schedule.teacher else schedule.subject.teacher.name,
            'room': schedule.room or 'Кабинет белгиленген эмес',
            'group': schedule.group.name,
            'time_slot': {
                'id': schedule.time_slot.id,
                'name': schedule.time_slot.name,
                'start_time': schedule.time_slot.start_time.strftime('%H:%M'),
                'end_time': schedule.time_slot.end_time.strftime('%H:%M'),
            },
            'can_edit': user_profile.role in ['ADMIN', 'MANAGER'],
            'can_mark_attendance': (
                user_profile.role == 'TEACHER' and 
                hasattr(request.user, 'teacher') and 
                (schedule.teacher == request.user.teacher if schedule.teacher else 
                 schedule.subject.teacher == request.user.teacher)
            ),
        }
    
    return JsonResponse({
        'schedule_data': schedule_data,
        'time_slots': [
            {
                'id': ts.id,
                'name': ts.name,
                'start_time': ts.start_time.strftime('%H:%M'),
                'end_time': ts.end_time.strftime('%H:%M'),
                'order': ts.order
            } for ts in time_slots
        ],
        'days': {
            'Monday': 'Дүйшөмбү',
            'Tuesday': 'Шейшемби', 
            'Wednesday': 'Шаршемби',
            'Thursday': 'Бейшемби',
            'Friday': 'Жума',
            'Saturday': 'Ишемби',
            'Sunday': 'Жекшемби',
        },
        'user_permissions': {
            'can_edit': user_profile.role in ['ADMIN', 'MANAGER'],
            'can_mark_attendance': user_profile.role == 'TEACHER',
            'is_student': user_profile.role == 'STUDENT',
            'is_parent': user_profile.role == 'PARENT',
        }
    })


@login_required
def get_groups_for_course(request):
    """Курс боюнча группаларды алуу (AJAX)"""
    course_id = request.GET.get('course_id')
    
    if not course_id:
        return JsonResponse({'error': 'Course ID керек'}, status=400)
    
    try:
        course = Course.objects.get(id=course_id)
        groups = Group.objects.filter(course=course).order_by('name')
        
        groups_data = [
            {
                'id': group.id,
                'name': group.name,
                'student_count': group.student_set.count(),
            } for group in groups
        ]
        
        return JsonResponse({
            'groups': groups_data,
            'course_name': course.name
        })
    
    except Course.DoesNotExist:
        return JsonResponse({'error': 'Курс табылган жок'}, status=404)


@csrf_exempt
@login_required
@user_passes_test(lambda u: u.userprofile.role in ['ADMIN', 'MANAGER'])
def save_schedule_lesson(request):
    """
    Сабакты сактоо/өзгөртүү (Админ/Менеджер үчүн)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST метод керек'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        lesson_id = data.get('lesson_id')
        subject_id = data.get('subject_id')
        teacher_id = data.get('teacher_id') 
        group_id = data.get('group_id')
        time_slot_id = data.get('time_slot_id')
        day = data.get('day')
        room = data.get('room', '')
        
        # Валидация
        if not all([subject_id, group_id, time_slot_id, day]):
            return JsonResponse({'error': 'Талапка сай бардык маалыматты толтуруңуз'}, status=400)
        
        # Объекттерди алуу
        subject = get_object_or_404(Subject, id=subject_id)
        group = get_object_or_404(Group, id=group_id)
        time_slot = get_object_or_404(TimeSlot, id=time_slot_id)
        teacher = get_object_or_404(Teacher, id=teacher_id) if teacher_id else None
        
        # Конфликттерди текшерүү
        conflicts = Schedule.objects.filter(
            group=group,
            day=day,
            time_slot=time_slot,
            is_active=True
        )
        
        if lesson_id:
            conflicts = conflicts.exclude(id=lesson_id)
        
        if conflicts.exists():
            return JsonResponse({'error': 'Бул убакытта группада башка сабак бар'}, status=400)
        
        # Мугалимдин конфликтин текшерүү (эгер teacher көрсөтүлгөн болсо)
        if teacher:
            teacher_conflicts = Schedule.objects.filter(
                teacher=teacher,
                day=day,
                time_slot=time_slot,
                is_active=True
            )
            
            if lesson_id:
                teacher_conflicts = teacher_conflicts.exclude(id=lesson_id)
            
            if teacher_conflicts.exists():
                return JsonResponse({'error': 'Бул убакытта мугалим башка группада сабак өтөт'}, status=400)
        
        # Сабакты сактоо же жаңылоо
        if lesson_id:
            # Өзгөртүү
            schedule = get_object_or_404(Schedule, id=lesson_id)
            schedule.subject = subject
            schedule.teacher = teacher
            schedule.group = group
            schedule.time_slot = time_slot
            schedule.day = day
            schedule.room = room
            schedule.save()
            
            message = 'Сабак ийгиликтүү өзгөртүлдү'
        else:
            # Жаңы кошуу
            schedule = Schedule.objects.create(
                subject=subject,
                teacher=teacher,
                group=group,
                time_slot=time_slot,
                day=day,
                room=room
            )
            
            message = 'Жаңы сабак ийгиликтүү кошулду'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'lesson_id': schedule.id
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON форматы туура эмес'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@login_required
@user_passes_test(lambda u: u.userprofile.role in ['ADMIN', 'MANAGER'])
def delete_schedule_lesson(request):
    """Сабакты өчүрүү"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST метод керек'}, status=405)
    
    try:
        data = json.loads(request.body)
        lesson_id = data.get('lesson_id')
        
        if not lesson_id:
            return JsonResponse({'error': 'Lesson ID керек'}, status=400)
        
        schedule = get_object_or_404(Schedule, id=lesson_id)
        schedule.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Сабак ийгиликтүү өчүрүлдү'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON форматы туура эмес'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(lambda u: u.userprofile.role == 'TEACHER')
def get_lesson_students(request):
    """Сабак үчүн студенттердин тизмесин алуу (Мугалим үчүн)"""
    lesson_id = request.GET.get('lesson_id')
    
    if not lesson_id:
        return JsonResponse({'error': 'Lesson ID керек'}, status=400)
    
    try:
        schedule = get_object_or_404(Schedule, id=lesson_id)
        
        # Уруксатты текшерүү
        teacher = Teacher.objects.get(user=request.user)
        if schedule.teacher != teacher and schedule.subject.teacher != teacher:
            return JsonResponse({'error': 'Бул сабакка жетки укугуңуз жок'}, status=403)
        
        students = Student.objects.filter(group=schedule.group).order_by('name')
        today = date.today()
        
        students_data = []
        for student in students:
            # Бүгүнкү катышуу статусун текшерүү
            today_attendance = Attendance.objects.filter(
                student=student,
                subject=schedule.subject,
                date=today
            ).first()
            
            students_data.append({
                'id': student.id,
                'name': student.name,
                'current_status': today_attendance.status if today_attendance else 'Present',
            })
        
        return JsonResponse({
            'students': students_data,
            'lesson_info': {
                'subject': schedule.subject.subject_name,
                'teacher': schedule.teacher.name if schedule.teacher else schedule.subject.teacher.name,
                'room': schedule.room,
                'time': f"{schedule.time_slot.start_time.strftime('%H:%M')} - {schedule.time_slot.end_time.strftime('%H:%M')}",
                'day': schedule.get_day_display(),
                'group': schedule.group.name,
            }
        })
        
    except Teacher.DoesNotExist:
        return JsonResponse({'error': 'Мугалим профили табылган жок'}, status=404)
    except Schedule.DoesNotExist:
        return JsonResponse({'error': 'Сабак табылган жок'}, status=404)


@csrf_exempt
@login_required
@user_passes_test(lambda u: u.userprofile.role == 'TEACHER')
def save_attendance(request):
    """Келүү-кетүү белгилөөнү сактоо"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST метод керек'}, status=405)
    
    try:
        data = json.loads(request.body)
        lesson_id = data.get('lesson_id')
        attendance_data = data.get('attendance', {})
        attendance_date = data.get('date', str(date.today()))
        
        if not lesson_id or not attendance_data:
            return JsonResponse({'error': 'Lesson ID жана attendance маалыматы керек'}, status=400)
        
        schedule = get_object_or_404(Schedule, id=lesson_id)
        
        # Уруксатты текшерүү
        teacher = Teacher.objects.get(user=request.user)
        if schedule.teacher != teacher and schedule.subject.teacher != teacher:
            return JsonResponse({'error': 'Бул сабакка жетки укугуңуз жок'}, status=403)
        
        # Attendance маалыматтарын сактоо
        attendance_date_obj = datetime.strptime(attendance_date, '%Y-%m-%d').date()
        
        for student_id, status in attendance_data.items():
            student = get_object_or_404(Student, id=student_id)
            
            attendance, created = Attendance.objects.update_or_create(
                student=student,
                subject=schedule.subject,
                date=attendance_date_obj,
                defaults={
                    'status': status,
                    'schedule': schedule,
                    'created_by': request.user,
                }
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Келүү-кетүү ийгиликтүү сакталды'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON форматы туура эмес'}, status=400)
    except Teacher.DoesNotExist:
        return JsonResponse({'error': 'Мугалим профили табылган жок'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)