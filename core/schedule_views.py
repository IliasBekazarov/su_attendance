"""
Жаңы Schedule систем view'лери
Талаптарга ылайык курс/группа фильтрациясы жана ролдор боюнча функциялар
"""

from django.shortcuts import render, redirect, get_object_or_404
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
    
    print(f"DEBUG: Initial query - Total active schedules: {schedules_query.count()}")
    
    if course_id:
        schedules_query = schedules_query.filter(group__course_id=course_id)
        print(f"DEBUG: After course filter (course_id={course_id}): {schedules_query.count()} schedules")
    
    if group_id:
        schedules_query = schedules_query.filter(group_id=group_id)
        print(f"DEBUG: After group filter (group_id={group_id}): {schedules_query.count()} schedules")
    
    schedules = schedules_query.order_by('day', 'time_slot__order')
    
    print(f"DEBUG: Final result: Found {schedules.count()} schedules for group_id={group_id}, course_id={course_id}")
    
    # Ар бир расписанинин деталдарын логго жазуу
    for schedule in schedules[:5]:  # Биринчи 5ин көрсөтүү
        print(f"DEBUG: Schedule {schedule.id}: {schedule.subject.subject_name} - Group {schedule.group.name} ({schedule.group.course.name}) - {schedule.day}")
    
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
    
    print(f"DEBUG get_groups_for_course: course_id={course_id}")
    
    if not course_id:
        return JsonResponse({'error': 'Course ID керек'}, status=400)
    
    try:
        groups_data = []
        groups = Group.objects.filter(course_id=course_id).select_related('course')
        
        for group in groups:
            # Студент саны
            student_count = group.student_set.count()
            groups_data.append({
                'id': group.id,
                'name': group.name,
                'course__name': group.course.name,
                'student_count': student_count
            })
        
        print(f"DEBUG get_groups_for_course: Found {len(groups_data)} groups")
        
        return JsonResponse({
            'groups': groups_data
        })
    except Exception as e:
        print(f"ERROR in get_groups_for_course: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@user_passes_test(lambda u: u.userprofile.role in ['ADMIN', 'MANAGER'])
@csrf_exempt
def save_schedule_lesson(request):
    """
    Сабакты сактоо/өзгөртүү (Админ/Менеджер үчүн)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST метод керек'}, status=405)
    
    try:
        print(f"DEBUG save_schedule_lesson: Request body: {request.body}")
        data = json.loads(request.body)
        print(f"DEBUG save_schedule_lesson: Parsed data: {data}")
        lesson_id = data.get('lesson_id')
        
        # Керектүү маалыматтарды алуу
        time_slot_id = data.get('time_slot_id')
        day = data.get('day')
        subject_id = data.get('subject_id')
        teacher_id = data.get('teacher_id')
        group_id = data.get('group_id')
        room = data.get('room', '')
        
        print(f"DEBUG save_schedule_lesson: time_slot_id={time_slot_id}, day={day}, subject_id={subject_id}, teacher_id={teacher_id}, group_id={group_id}, room={room}")
        
        if not all([time_slot_id, day, subject_id, group_id]):
            missing_fields = []
            if not time_slot_id: missing_fields.append('time_slot_id')
            if not day: missing_fields.append('day')
            if not subject_id: missing_fields.append('subject_id')
            if not group_id: missing_fields.append('group_id')
            
            error_msg = f'Төмөнкү талаалар толтурулган жок: {", ".join(missing_fields)}'
            print(f"DEBUG save_schedule_lesson: Missing fields error: {error_msg}")
            return JsonResponse({'error': error_msg}, status=400)
        
        # Объекттерди алуу
        time_slot = get_object_or_404(TimeSlot, id=time_slot_id, is_active=True)
        subject = get_object_or_404(Subject, id=subject_id)
        group = get_object_or_404(Group, id=group_id)
        teacher = get_object_or_404(Teacher, id=teacher_id) if teacher_id else None
        
        print(f"DEBUG save_schedule_lesson: Objects found - time_slot={time_slot}, subject={subject}, group={group}, teacher={teacher}")
        
        # Конфликттерди текшерүү
        existing_schedule = Schedule.objects.filter(
            group=group,
            day=day,
            time_slot=time_slot,
            is_active=True
        ).exclude(id=lesson_id if lesson_id else None).first()
        
        print(f"DEBUG save_schedule_lesson: Existing schedule check: {existing_schedule}")
        
        if existing_schedule:
            return JsonResponse({
                'error': f'Бул убакытта {group.name} группасында башка сабак бар'
            }, status=400)
        
        # Мугалим конфликтин текшерүү
        if teacher:
            teacher_conflict = Schedule.objects.filter(
                teacher=teacher,
                day=day,
                time_slot=time_slot,
                is_active=True
            ).exclude(id=lesson_id if lesson_id else None).first()
            
            if teacher_conflict:
                return JsonResponse({
                    'error': f'Мугалим {teacher.name} бул убакытта башка сабакта бар'
                }, status=400)
        
        # Сактоо же жаңылоо
        if lesson_id:
            # Жаңылоо
            schedule = get_object_or_404(Schedule, id=lesson_id)
            schedule.time_slot = time_slot
            schedule.day = day
            schedule.subject = subject
            schedule.teacher = teacher
            schedule.group = group
            schedule.room = room
            schedule.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Сабак ийгиликтүү жаңыланды',
                'lesson_id': schedule.id
            })
        else:
            # Жаңы кошуу
            schedule = Schedule.objects.create(
                time_slot=time_slot,
                day=day,
                subject=subject,
                teacher=teacher,
                group=group,
                room=room,
                is_active=True
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Жаңы сабак ийгиликтүү кошулду',
                'lesson_id': schedule.id
            })
            
    except json.JSONDecodeError:
        print("DEBUG save_schedule_lesson: JSON decode error")
        return JsonResponse({'error': 'JSON форматы туура эмес'}, status=400)
    except Exception as e:
        print(f"DEBUG save_schedule_lesson: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@user_passes_test(lambda u: u.userprofile.role in ['ADMIN', 'MANAGER'])
@csrf_exempt
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
        schedule.is_active = False
        schedule.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Сабак ийгиликтүү өчүрүлдү'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON форматы туура эмес'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@user_passes_test(lambda u: u.userprofile.role == 'TEACHER')
def get_lesson_students(request):
    """Сабак үчүн студенттердин тизмесин алуу (Мугалим үчүн)"""
    lesson_id = request.GET.get('lesson_id')
    
    if not lesson_id:
        return JsonResponse({'error': 'Lesson ID керек'}, status=400)
    
    try:
        schedule = get_object_or_404(Schedule, id=lesson_id, is_active=True)
        
        # Мугалимдин укугун текшерүү
        user_teacher = Teacher.objects.get(user=request.user)
        if schedule.teacher != user_teacher and schedule.subject.teacher != user_teacher:
            return JsonResponse({'error': 'Сизде бул сабакка жетүү укугу жок'}, status=403)
        
        # Группанын студенттерин алуу
        students = Student.objects.filter(
            group=schedule.group,
            is_active=True
        ).select_related('user').order_by('user__last_name', 'user__first_name')
        
        students_data = []
        for student in students:
            # Бул күндүн келүү-кетүүсүн алуу
            today = date.today()
            attendance = Attendance.objects.filter(
                student=student,
                schedule=schedule,
                date=today
            ).first()
            
            students_data.append({
                'id': student.id,
                'name': f"{student.user.last_name} {student.user.first_name}",
                'student_id': student.student_id,
                'attendance_status': attendance.status if attendance else None,
                'attendance_id': attendance.id if attendance else None,
            })
        
        return JsonResponse({
            'students': students_data,
            'lesson': {
                'id': schedule.id,
                'subject': schedule.subject.subject_name,
                'group': schedule.group.name,
                'time_slot': schedule.time_slot.name,
                'day': schedule.get_day_display(),
                'room': schedule.room,
            }
        })
        
    except Teacher.DoesNotExist:
        return JsonResponse({'error': 'Мугалим профили табылган жок'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@user_passes_test(lambda u: u.userprofile.role == 'TEACHER')
@csrf_exempt
def save_attendance(request):
    """Келүү-кетүү маалыматтарын сактоо"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST метод керек'}, status=405)
    
    try:
        data = json.loads(request.body)
        lesson_id = data.get('lesson_id')
        attendance_data = data.get('attendance_data', {})
        
        if not lesson_id or not attendance_data:
            return JsonResponse({'error': 'Lesson ID жана attendance data керек'}, status=400)
        
        schedule = get_object_or_404(Schedule, id=lesson_id, is_active=True)
        
        # Мугалимдин укугун текшерүү
        user_teacher = Teacher.objects.get(user=request.user)
        if schedule.teacher != user_teacher and schedule.subject.teacher != user_teacher:
            return JsonResponse({'error': 'Сизде бул сабакка жетүү укугу жок'}, status=403)
        
        today = date.today()
        saved_count = 0
        
        for student_id, status in attendance_data.items():
            try:
                student = Student.objects.get(id=student_id, group=schedule.group, is_active=True)
                
                # Келүү-кетүү жазуусун алуу же түзүү
                attendance, created = Attendance.objects.get_or_create(
                    student=student,
                    schedule=schedule,
                    date=today,
                    defaults={
                        'status': status,
                        'marked_by': request.user,
                        'marked_at': datetime.now()
                    }
                )
                
                if not created:
                    attendance.status = status
                    attendance.marked_by = request.user
                    attendance.marked_at = datetime.now()
                    attendance.save()
                
                saved_count += 1
                
            except Student.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True,
            'message': f'{saved_count} студенттин келүү-кетүүсү сакталды'
        })
        
    except Teacher.DoesNotExist:
        return JsonResponse({'error': 'Мугалим профили табылган жок'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON форматы туура эмес'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)