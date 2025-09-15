from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q, Count
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile, Student, Teacher, Course, Group, Attendance, Notification, Subject, Schedule, LeaveRequest
from .forms import StudentRegistrationForm, NotificationForm, LeaveRequestForm
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from datetime import datetime, date, timedelta
from dal import autocomplete
from django import forms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# ============= NOTIFICATION HELPER FUNCTIONS =============

def create_notification(recipient, notification_type, title, message, sender=None, student=None, leave_request=None):
    """Билдирме түзүү үчүн helper функция"""
    return Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        title=title,
        message=message,
        student=student,
        leave_request=leave_request
    )

def check_excessive_absences():
    """Көп жолу келбеген студенттер үчүн билдирмелер жөнөтүү"""
    from collections import defaultdict
    
    # Соңку 10 күндө 3 жолудан көп келбеген студенттерди тапуу
    last_10_days = date.today() - timedelta(days=10)
    
    student_absences = defaultdict(int)
    recent_absences = Attendance.objects.filter(
        date__gte=last_10_days,
        status='Absent'
    )
    
    for absence in recent_absences:
        student_absences[absence.student] += 1
    
    # 3тен көп жок болгон студенттер үчүн билдирме
    for student, absence_count in student_absences.items():
        if absence_count >= 3:
            # Ошол студенттин ата-энелерине билдирме жөнөтүү
            parent_profiles = student.parents.all()
            for parent_profile in parent_profiles:
                create_notification(
                    recipient=parent_profile.user,
                    notification_type='ABSENCE',
                    title=f'⚠️ {student.name} көп жолу келбеди',
                    message=f'Сиздин балаңыз {student.name} соңку 10 күн ичинде {absence_count} жолу сабактан келген жок. Анын себебин аныктап, зарыл чараларды көрүүгө өтүнөбүз.',
                    student=student
                )
            
            # Класс жетекчисине да билдирме
            if student.group:
                # Студенттин группасы менен иштеген мугалимдерди тапуу
                group_teachers = Teacher.objects.filter(
                    subject__schedule__group=student.group
                ).distinct()
                
                for teacher in group_teachers:
                    if teacher.user:
                        create_notification(
                            recipient=teacher.user,
                            notification_type='ABSENCE',
                            title=f'⚠️ {student.name} көп жолу келбеди',
                            message=f'Студент {student.name} ({student.group.name}) соңку 10 күн ичинде {absence_count} жолу сабактан келген жок.',
                            student=student
                        )

def send_leave_request_notification(leave_request):
    """Бошотуу сурамы жөнөтүлгөндө билдирме"""
    # Администраторлорго жана менеджерлерге билдирме
    admins_and_managers = User.objects.filter(
        userprofile__role__in=['ADMIN', 'MANAGER']
    )
    
    for admin in admins_and_managers:
        create_notification(
            recipient=admin,
            notification_type='LEAVE_REQUEST',
            title=f'📝 Жаңы бошотуу сурамы - {leave_request.student.name}',
            message=f'Студент {leave_request.student.name} ({leave_request.student.group.name}) {leave_request.start_date} - {leave_request.end_date} мөөнөтүндө {leave_request.get_leave_type_display()} себебинен бошотуу сурап жатат.\n\nСебеби: {leave_request.reason}',
            sender=leave_request.student.user,
            student=leave_request.student,
            leave_request=leave_request
        )

def send_leave_decision_notification(leave_request, approved_by):
    """Бошотуу сурамы боюнча чечим кабыл алынгандан кийин билдирме"""
    status_text = 'бекитилди' if leave_request.status == 'APPROVED' else 'четке кагылды'
    emoji = '✅' if leave_request.status == 'APPROVED' else '❌'
    
    # Студентке билдирме
    create_notification(
        recipient=leave_request.student.user,
        notification_type='LEAVE_APPROVED' if leave_request.status == 'APPROVED' else 'LEAVE_REJECTED',
        title=f'{emoji} Бошотуу сурамыңыз {status_text}',
        message=f'Сиздин {leave_request.start_date} - {leave_request.end_date} мөөнөтүндөгү бошотуу сурамыңыз {status_text}.\n\nЧечим кабыл алган: {approved_by.get_full_name() or approved_by.username}',
        sender=approved_by,
        student=leave_request.student,
        leave_request=leave_request
    )
    
    # Ата-энелерге да билдирме
    parent_profiles = leave_request.student.parents.all()
    for parent_profile in parent_profiles:
        create_notification(
            recipient=parent_profile.user,
            notification_type='LEAVE_APPROVED' if leave_request.status == 'APPROVED' else 'LEAVE_REJECTED',
            title=f'{emoji} {leave_request.student.name}дын бошотуу сурамы {status_text}',
            message=f'Балаңыздын {leave_request.start_date} - {leave_request.end_date} мөөнөтүндөгү бошотуу сурамы {status_text}.\n\nЧечим кабыл алган: {approved_by.get_full_name() or approved_by.username}',
            sender=approved_by,
            student=leave_request.student,
            leave_request=leave_request
        )

@login_required
def mark_schedule_attendance(request, group_id, period):
    if request.user.userprofile.role != 'TEACHER':
        return JsonResponse({'error': 'Бул функция мугалимдер үчүн гана.'}, status=403)
    
    group = get_object_or_404(Group, id=group_id)
    students = Student.objects.filter(group=group)
    today = date.today()
    
    data = {
        'group_name': group.name,
        'students': [
            {
                'id': student.id,
                'name': student.name,
                'attendance': Attendance.objects.filter(
                    student=student, schedule__group=group, schedule__day=today.weekday(), date=today
                ).exists()
            } for student in students
        ]
    }
    return JsonResponse(data)

@csrf_exempt
@login_required
def submit_schedule_attendance(request):
    if request.user.userprofile.role != 'TEACHER':
        return JsonResponse({'error': 'Бул функция мугалимдер үчүн гана.'}, status=403)
    
    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('status_'):
                student_id = key.replace('status_', '')
                student = get_object_or_404(Student, id=student_id)
                schedule_id = request.POST.get('schedule_id')
                schedule = get_object_or_404(Schedule, id=schedule_id)
                Attendance.objects.update_or_create(
                    student=student,
                    schedule=schedule,
                    date=date.today(),
                    defaults={'status': value or 'Absent', 'created_by': request.user}
                )
            elif key.startswith('late_'):
                student_id = key.replace('late_', '')
                student = get_object_or_404(Student, id=student_id)
                schedule_id = request.POST.get('schedule_id')
                schedule = get_object_or_404(Schedule, id=schedule_id)
                if value:
                    Attendance.objects.update_or_create(
                        student=student,
                        schedule=schedule,
                        date=date.today(),
                        defaults={'status': value, 'created_by': request.user}
                    )
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)
# Форма
class NotificationForm(forms.ModelForm):
    student = forms.ModelChoiceField(queryset=Student.objects.all(), label='Студент')
    message = forms.CharField(widget=forms.Textarea, label='Билдирүү')

    class Meta:
        model = Notification
        fields = ['student', 'message']

# Autocomplete
class UserProfileAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return UserProfile.objects.none()
        qs = UserProfile.objects.filter(role='PARENT')
        if self.q:
            qs = qs.filter(user__username__istartswith=self.q)
        return qs

# Ролдорду текшерүү
def is_admin_or_manager(user):
    try:
        return user.userprofile.role in ['ADMIN', 'MANAGER']
    except:
        return False

def is_teacher(user):
    try:
        return user.userprofile.role == 'TEACHER'
    except:
        return False

# View'дор
def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

@csrf_exempt
def register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, role='STUDENT')
            student = Student.objects.create(
                user=user,
                name=form.cleaned_data['name'],
                course=form.cleaned_data['course'],
                group=form.cleaned_data['group']
            )
            parent_username = form.cleaned_data.get('parent_username')
            if parent_username:
                parent = User.objects.get(username=parent_username)
                student.parents.add(parent.userprofile)
                parent.userprofile.students.add(student)
                messages.success(request, 'Ата-эне байланыштырылды!')
            messages.success(request, 'Студент катталды!')
            login(request, user)
            return redirect('dashboard')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = StudentRegistrationForm()
    return render(request, 'registration.html', {'form': form})

from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def user_login(request):
    if request.method == 'POST':
        # CSRF debug маалыматы
        print(f"POST request from user: {request.user}")
        print(f"CSRF cookie: {request.META.get('CSRF_COOKIE')}")
        print(f"POST CSRF token: {request.POST.get('csrfmiddlewaretoken')}")
        
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Кирүү катасы!')
    return render(request, 'login.html')

def user_logout(request):
    auth_logout(request)
    messages.success(request, 'Сиз чыктыңыз!')
    return redirect('login')

@login_required
@login_required
def dashboard(request):
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    print(f"Dashboard view called for user: {request.user}")
    
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'STUDENT'})
        if created:
            messages.info(request, 'Профилиңиз автоматтык түрдө түзүлдү (STUDENT ролу).')
        role = profile.role
        print(f"User role: {role}")
    except Exception as e:
        print(f"Error getting user profile: {e}")
        return HttpResponse(f"Error: {e}", status=500)
    
    # Бүгүнкү дата
    today = timezone.now().date()
    today_weekday_num = today.weekday()  # 0=Monday, 6=Sunday
    
    # Күндөрдү Django Schedule моделинин форматына алмаштыруу
    weekday_map = {
        0: 'MONDAY',
        1: 'TUESDAY', 
        2: 'WEDNESDAY',
        3: 'THURSDAY',
        4: 'FRIDAY',
        5: 'SATURDAY',
        6: 'SUNDAY'
    }
    today_weekday = weekday_map.get(today_weekday_num, 'MONDAY')
    
    context = {
        'role': role, 
        'today': today,
        'user': request.user
    }
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if role in ['ADMIN', 'MANAGER']:
        # Статистика маалыматтары
        total_students = Student.objects.count()
        total_teachers = Teacher.objects.count()
        total_groups = Group.objects.count()
        total_subjects = Subject.objects.count()
        
        # Соңку иш-аракеттер
        recent_activities = []
        
        context.update({
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_groups': total_groups,
            'total_subjects': total_subjects,
            'recent_activities': recent_activities,
        })
        
    elif role == 'TEACHER':
        # Мугалим профилин алуу
        try:
            teacher = Teacher.objects.get(user=request.user)
            context['teacher_obj'] = teacher
            
            # Мугалимдин предметтери
            my_subjects = Subject.objects.filter(teacher=teacher)
            my_subjects_count = my_subjects.count()
            
            # Мугалимдин студенттери (группалар аркылуу)
            my_groups = Group.objects.filter(schedule__subject__teacher=teacher).distinct()
            my_students = Student.objects.filter(group__in=my_groups)
            my_students_count = my_students.count()
            
            # Бүгүнкү расписание
            today_schedule = Schedule.objects.filter(
                subject__teacher=teacher,
                day=today_weekday
            ).order_by('start_time')
            
            today_classes_count = today_schedule.count()
            
            context.update({
                'my_subjects_count': my_subjects_count,
                'my_students_count': my_students_count,
                'today_classes_count': today_classes_count,
                'today_schedule': today_schedule,
            })
            
        except Teacher.DoesNotExist:
            messages.error(request, 'Мугалим профили табылган жок. Администраторго кайрылыңыз.')
            
    elif role == 'STUDENT':
        # Студент профилин алуу же түзүү
        student, created = Student.objects.get_or_create(
            user=request.user,
            defaults={
                'name': request.user.get_full_name() or request.user.username,
                'course': Course.objects.first(),
                'group': Group.objects.first()
            }
        )
        
        if created and not Course.objects.exists():
            Course.objects.create(name='1-курс', year=2024)
        if created and not Group.objects.exists():
            course = Course.objects.first()
            Group.objects.create(name='А-группа', course=course)
            
        context['student_obj'] = student
        
        # Катышуу статистикасы
        attendance = Attendance.objects.filter(student=student)
        if start_date:
            attendance = attendance.filter(date__gte=start_date)
        if end_date:
            attendance = attendance.filter(date__lte=end_date)
            
        total_attendance = attendance.count()
        present_days = attendance.filter(status='Present').count()
        absent_days = attendance.filter(status='Absent').count()
        excused_days = attendance.filter(status='Excused').count()
        
        attendance_percentage = (present_days / total_attendance * 100) if total_attendance > 0 else 0
        
        # Бүгүнкү расписание
        student_today_schedule = []
        if student.group:
            student_today_schedule = Schedule.objects.filter(
                group=student.group,
                day=today_weekday
            ).order_by('start_time')
            
            # Ар бир сабак үчүн катышуу статусун алуу
            for schedule in student_today_schedule:
                try:
                    attendance_record = Attendance.objects.get(
                        student=student,
                        date=today,
                        subject=schedule.subject
                    )
                    schedule.attendance_status = attendance_record.status
                except Attendance.DoesNotExist:
                    schedule.attendance_status = None
        
        context.update({
            'attendance_percentage': round(attendance_percentage, 1),
            'present_days': present_days,
            'absent_days': absent_days,
            'excused_days': excused_days,
            'student_today_schedule': student_today_schedule,
            'start_date': start_date,
            'end_date': end_date
        })
        
    elif role == 'PARENT':
        # Ата-энелердин балдары
        my_children = profile.students.all()
        
        if my_children:
            # Ар бир бала үчүн статистика
            for child in my_children:
                attendance = Attendance.objects.filter(student=child)
                if start_date:
                    attendance = attendance.filter(date__gte=start_date)
                if end_date:
                    attendance = attendance.filter(date__lte=end_date)
                    
                total_attendance = attendance.count()
                present_count = attendance.filter(status='Present').count()
                absent_count = attendance.filter(status='Absent').count()
                
                child.present_count = present_count
                child.absent_count = absent_count
                child.attendance_percentage = (present_count / total_attendance * 100) if total_attendance > 0 else 0
            
            # Ата-энелер үчүн билдирүүлөр
            parent_notifications = Notification.objects.filter(
                recipient=request.user,
                notification_type__in=['ABSENCE', 'LEAVE_REQUEST', 'GENERAL']
            ).order_by('-created_at')[:10]
            
            context.update({
                'my_children': my_children,
                'parent_notifications': parent_notifications,
                'start_date': start_date,
                'end_date': end_date
            })
        else:
            messages.error(request, 'Балаңыздын профили байланыштырылган эмес. Администраторго кайрылыңыз.')
            context.update({'message': 'Баланын маалыматы жок'})

    print(f"Dashboard context keys: {list(context.keys())}")
    print(f"Rendering dashboard.html template")
    
    # Context маалыматтарын толук чыгаралы  
    print(f"Student object: {context.get('student_obj')}")
    if 'student_obj' in context and context['student_obj']:
        student = context['student_obj']
        print(f"Student details: name={student.name}, group={student.group}")
        if hasattr(student, 'group') and student.group:
            print(f"Group details: {student.group.name}")
    
    try:
        response = render(request, 'dashboard.html', context)
        print(f"Template rendered successfully, content length: {len(response.content)}")
        return response
    except Exception as e:
        print(f"Template rendering error: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return HttpResponse(f"Template error: {e}", status=500)

@login_required
def send_notification(request):
    if request.user.userprofile.role != 'TEACHER':
        messages.error(request, 'Бул функция мугалимдер үчүн гана.')
        return redirect('dashboard')
    
    teacher = Teacher.objects.get(user=request.user)
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.teacher = teacher
            notification.save()
            messages.success(request, 'Билдирүү жөнөтүлдү!')
            return redirect('dashboard')
    else:
        form = NotificationForm()
    return render(request, 'send_notification.html', {'form': form})

@login_required
def mark_notification_read(request, notification_id):
    if request.user.userprofile.role != 'PARENT':
        messages.error(request, 'Бул функция ата-энелер үчүн гана.')
        return redirect('dashboard')
    notification = Notification.objects.get(id=notification_id)
    if notification.student in request.user.userprofile.students.all():
        notification.is_read = True
        notification.save()
        messages.success(request, 'Билдирүү окулду деп белгиленди.')
    return redirect('dashboard')

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Schedule, Subject, Group
from .forms import ScheduleEditForm  # Форма файлын импорттоо

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Schedule, Subject, Group
from .forms import ScheduleEditForm  # Жаңы кошулган

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Course, Group, Schedule, Teacher, Attendance, Student, Subject
from datetime import date
import json

@login_required
@login_required
def schedule_edit(request):
    """Расписание көрүү (Менеджер/Админ үчүн - жөн гана көрүү режими)"""
    profile = UserProfile.objects.get(user=request.user)
    
    # Уруксат текшерүү - жөн гана көрүү үчүн
    if profile.role not in ['MANAGER', 'ADMIN']:
        messages.error(request, 'Бул функция менеджер жана админдер үчүн гана.')
        return redirect('dashboard')

    schedules = Schedule.objects.all()  # Бардык расписаниелер
    courses = Course.objects.all()
    
    # Убакыт периоддору (статик)
    periods = []
    times = [
        ('08:00', '09:30'),
        ('09:40', '11:10'), 
        ('11:30', '13:00'),
        ('14:00', '15:30'),
        ('15:40', '17:10')
    ]
    
    for i, (start, end) in enumerate(times, 1):
        from datetime import datetime
        start_time = datetime.strptime(start, '%H:%M').time()
        end_time = datetime.strptime(end, '%H:%M').time()
        periods.append({
            'period': i,
            'start_time': start_time,
            'end_time': end_time
        })

    # Көрүү режиминде POST өндөшүү жок - жөн гана маалымат көрсөтүү
    context = {
        'courses': courses,
        'active_course': courses.first() if courses.exists() else None,
        'periods': periods,
        'schedules': schedules,
        'view_only': True,  # Көрүү режими белгиси
    }
    return render(request, 'schedule_edit.html', context)

@login_required
def schedule_update(request):
    if request.method == 'POST' and request.user.userprofile.role == 'MANAGER':
        try:
            data = json.loads(request.body)
            group_id = data.get('group_id')
            period = data.get('period')
            content = data.get('content')

            # Расписаниени жаңылоо логикасы
            # Мисалы, content'ти бөлүп, subject, teacher жана room'ду сактоо
            lines = content.strip().split('\n')
            subject_name = lines[0] if lines else ''
            teacher_name = lines[1] if len(lines) > 1 else ''
            room = lines[2] if len(lines) > 2 else ''

            group = get_object_or_404(Group, id=group_id)
            subject = Subject.objects.filter(subject_name=subject_name).first()
            teacher = Teacher.objects.filter(name=teacher_name).first()

            Schedule.objects.update_or_create(
                group=group,
                period=period,
                defaults={
                    'subject': subject,
                    'teacher': teacher,
                    'room': room,
                    'start_time': '10:00',  # Убакытты моделден же periods тизмесинен алса болот
                    'end_time': '11:20'
                }
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def student_schedule(request):
    if request.user.userprofile.role != 'STUDENT':
        messages.error(request, 'Бул функция студенттер үчүн гана.')
        return redirect('dashboard')
    
    student = Student.objects.get(user=request.user)
    schedules = Schedule.objects.filter(group=student.group)
    context = {'schedules': schedules}
    return render(request, 'student_schedule.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Course, Group, Schedule, Teacher, Attendance, Student
from datetime import date

@login_required
def teacher_schedule(request):
    """Мугалимдин расписаниесин көрүү жана жоктоо белгилөө"""
    if request.user.userprofile.role != 'TEACHER':
        messages.error(request, 'Бул функция мугалимдер үчүн гана.')
        return redirect('dashboard')
    
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Сиз мугалим катары катталган эмессиз.')
        return redirect('dashboard')

    # Мугалимдин сабактары гана чыгарылат
    schedules = Schedule.objects.filter(
        subject__teacher=teacher
    ).select_related('subject', 'group', 'group__course').order_by('day', 'start_time')
    
    # Курстарды алуу
    courses = Course.objects.filter(
        group__schedule__subject__teacher=teacher
    ).distinct().order_by('year')

    # Күндөр тизмеси
    days = [
        ('Monday', 'Дүйшөмбү'),
        ('Tuesday', 'Шейшемби'), 
        ('Wednesday', 'Шаршемби'),
        ('Thursday', 'Бейшемби'),
        ('Friday', 'Жума'),
        ('Saturday', 'Ишемби'),
    ]

    context = {
        'teacher': teacher,
        'schedules': schedules,
        'courses': courses,
        'days': days,
    }
    return render(request, 'teacher_schedule.html', context)

@login_required
def teacher_attendance(request):
    """Мугалим үчүн жеке жоктоо системасы"""
    if request.user.userprofile.role != 'TEACHER':
        messages.error(request, 'Бул функция мугалимдер үчүн гана.')
        return redirect('dashboard')
    
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Сиз мугалим катары катталган эмессиз.')
        return redirect('dashboard')

    # POST request - жоктоо белгилөө
    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        if schedule_id:
            schedule = get_object_or_404(Schedule, id=schedule_id, subject__teacher=teacher)
            
            saved_count = 0
            for key, value in request.POST.items():
                if key.startswith('status_') and value:
                    try:
                        student_id = key.replace('status_', '')
                        student = get_object_or_404(Student, id=student_id, group=schedule.group)
                        
                        # Attendance сактоо
                        attendance, created = Attendance.objects.update_or_create(
                            student=student,
                            subject=schedule.subject,
                            schedule=schedule,
                            date=date.today(),
                            defaults={
                                'status': value, 
                                'created_by': request.user
                            }
                        )
                        saved_count += 1
                        
                    except (Student.DoesNotExist, ValueError):
                        continue
            
            if saved_count > 0:
                messages.success(request, f'{saved_count} студенттин катышуусу белгиленди.')
            else:
                messages.warning(request, 'Эч кандай маалымат сакталган жок.')
                
            return redirect('teacher_attendance')

    # GET request - мугалимдин сабактарын көрсөтүү
    schedules = Schedule.objects.filter(
        subject__teacher=teacher
    ).select_related(
        'subject', 'group', 'group__course'
    ).prefetch_related(
        'group__student_set'
    ).order_by('day', 'start_time')
    
    # Статистика эсептөө
    total_students = sum([schedule.group.student_set.count() for schedule in schedules])
    unique_groups = schedules.values('group').distinct().count()
    subjects = schedules.values('subject').distinct()

    context = {
        'teacher': teacher,
        'schedules': schedules,
        'total_students': total_students,
        'unique_groups': unique_groups,
        'subjects': subjects,
        'today': date.today(),
    }
    return render(request, 'teacher_attendance.html', context)
@login_required
def mark_attendance(request, subject_id):
    if request.user.userprofile.role not in ['TEACHER', 'ADMIN', 'MANAGER']:
        messages.error(request, 'Бул функция мугалимдер же администраторлор үчүн гана.')
        return redirect('dashboard')
    
    subject = get_object_or_404(Subject, id=subject_id)
    students = Student.objects.filter(group=subject.course.group_set.first())
    
    if request.method == 'POST':
        for student in students:
            status = request.POST.get(f'status_{student.id}')
            if status:
                Attendance.objects.create(
                    student=student,
                    subject=subject,
                    date=date.today(),
                    status=status,
                    created_by=request.user
                )
        messages.success(request, 'Катышуу белгиленди.')
        return redirect('schedule')  # Бул жерде багыттоо туура эмес, анткени 'schedule' жок. 'dashboard' же 'teacher_schedule' колдонуңуз.
    
    context = {'subject': subject, 'students': students}
    return render(request, 'mark_attendance.html', context)

@login_required
def mark_group_attendance(request, schedule_id):
    if request.user.userprofile.role != 'TEACHER':
        messages.error(request, 'Бул функция мугалимдер үчүн гана.')
        return redirect('dashboard')
    
    schedule = get_object_or_404(Schedule, id=schedule_id)
    students = Student.objects.filter(group=schedule.group)
    
    if request.method == 'POST':
        for student in students:
            status = request.POST.get(f'status_{student.id}')
            if status:
                Attendance.objects.update_or_create(
                    student=student,
                    subject=schedule.subject,  # Subject кошуу
                    schedule=schedule,
                    date=date.today(),
                    defaults={'status': status, 'created_by': request.user}
                )
        messages.success(request, 'Катышуу белгиленди.')
        return redirect('teacher_schedule')
    
    context = {'schedule': schedule, 'students': students}
    return render(request, 'mark_group_attendance.html', context)

@login_required
@user_passes_test(is_admin_or_manager)
def report(request):
    from django.utils import timezone
    from datetime import datetime, timedelta
    import json
    
    # Дата фильтри
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    report_type = request.GET.get('report_type', 'all')  # all, daily, weekly, monthly
    student_id = request.GET.get('student')
    group_id = request.GET.get('group')
    
    # Базалык attendance queryset
    attendances = Attendance.objects.all()
    
    # Дата боюнча фильтр
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            attendances = attendances.filter(date__gte=start_date)
        except ValueError:
            start_date = None
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            attendances = attendances.filter(date__lte=end_date)
        except ValueError:
            end_date = None
    
    # Студент боюнча фильтр
    if student_id:
        try:
            attendances = attendances.filter(student_id=student_id)
        except:
            pass
    
    # Группа боюнча фильтр
    if group_id:
        try:
            attendances = attendances.filter(student__group_id=group_id)
        except:
            pass
    
    # Быстрые фильтры
    today = timezone.now().date()
    if report_type == 'daily':
        attendances = attendances.filter(date=today)
    elif report_type == 'weekly':
        week_start = today - timedelta(days=today.weekday())
        attendances = attendances.filter(date__gte=week_start, date__lte=today)
    elif report_type == 'monthly':
        month_start = today.replace(day=1)
        attendances = attendances.filter(date__gte=month_start, date__lte=today)
    
    # Статистика
    total_records = attendances.count()
    present_count = attendances.filter(status='Present').count()
    absent_count = attendances.filter(status='Absent').count()
    late_count = attendances.filter(status='Late').count()
    excused_count = attendances.filter(status='Excused').count()
    
    attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0
    
    # Группа боюнча статистика
    group_stats = []
    for group in Group.objects.all():
        group_attendances = attendances.filter(student__group=group)
        group_total = group_attendances.count()
        group_present = group_attendances.filter(status='Present').count()
        group_percentage = (group_present / group_total * 100) if group_total > 0 else 0
        
        group_stats.append({
            'group': group,
            'total': group_total,
            'present': group_present,
            'percentage': round(group_percentage, 1)
        })
    
    # Күнүмдүк тренд (соңку 7 күн)
    daily_trend = []
    for i in range(7):
        check_date = today - timedelta(days=i)
        day_attendances = Attendance.objects.filter(date=check_date)
        day_total = day_attendances.count()
        day_present = day_attendances.filter(status='Present').count()
        day_percentage = (day_present / day_total * 100) if day_total > 0 else 0
        
        daily_trend.append({
            'date': check_date.strftime('%m-%d'),
            'percentage': round(day_percentage, 1),
            'total': day_total
        })
    
    daily_trend.reverse()  # Хронологиялык тартипте
    
    # Эң көп жок болгон студенттер
    from django.db.models import Count
    top_absent_students = Student.objects.annotate(
        absent_count=Count('attendance', filter=Q(attendance__status='Absent'))
    ).filter(absent_count__gt=0).order_by('-absent_count')[:10]
    
    # Export handling
    if request.method == 'POST':
        format_type = request.POST.get('format')
        if format_type == 'pdf':
            return export_detailed_pdf(attendances, {
                'report_type': report_type,
                'start_date': start_date,
                'end_date': end_date,
                'total_records': total_records,
                'present_count': present_count,
                'absent_count': absent_count,
                'late_count': late_count,
                'excused_count': excused_count,
                'attendance_percentage': attendance_percentage
            })
        elif format_type == 'excel':
            return export_detailed_excel(attendances)
    
    context = {
        'attendances': attendances.order_by('-date')[:100],  # Show latest 100
        'total_records': total_records,
        'present_count': present_count,
        'absent_count': absent_count, 
        'late_count': late_count,
        'excused_count': excused_count,
        'attendance_percentage': round(attendance_percentage, 1),
        'group_stats': group_stats,
        'daily_trend': json.dumps(daily_trend),
        'top_absent_students': top_absent_students,
        'students': Student.objects.all(),
        'groups': Group.objects.all(),
        'start_date': start_date,
        'end_date': end_date,
        'report_type': report_type,
        'student_id': student_id,
        'group_id': group_id,
    }
    
    return render(request, 'report.html', context)

def export_detailed_pdf(attendances, stats):
    """Детальный PDF отчет с статистикой"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="detailed_attendance_report.pdf"'
    
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfutils
    from reportlab.lib.units import inch
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center
    )
    elements.append(Paragraph("Катышуу Системасы - Детальный Отчет", title_style))
    elements.append(Spacer(1, 20))
    
    # Statistics Summary
    summary_data = [
        ['Жалпы жазуулар:', stats['total_records']],
        ['Катышкандар:', stats['present_count']],
        ['Катышпагандар:', stats['absent_count']], 
        ['Кечиккендер:', stats['late_count']],
        ['Уруксат менен жоктор:', stats['excused_count']],
        ['Катышуу пайызы:', f"{stats['attendance_percentage']}%"],
    ]
    
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Attendance Records Table
    if attendances.exists():
        elements.append(Paragraph("Катышуу Жазуулары", styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        data = [['Студент', 'Сабак', 'Дата', 'Статус']]
        for att in attendances[:50]:  # Limit to 50 records for PDF
            data.append([
                att.student.name,
                att.subject.subject_name if att.subject else 'Н/Д',
                att.date.strftime('%d.%m.%Y'),
                att.get_status_display()
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
    
    doc.build(elements)
    return response

def export_detailed_excel(attendances):
    """Детальный Excel отчет"""
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="detailed_attendance_report.xlsx"'
    
    workbook = Workbook()
    
    # Main data sheet
    worksheet = workbook.active
    worksheet.title = "Катышуу Жазуулары"
    
    # Headers
    headers = ['Студент', 'Группа', 'Сабак', 'Дата', 'Статус', 'Жаратылган күнү', 'Жараткан']
    for col_num, header in enumerate(headers, 1):
        worksheet.cell(row=1, column=col_num, value=header)
    
    # Data
    for row_num, att in enumerate(attendances, 2):
        worksheet.cell(row=row_num, column=1, value=att.student.name)
        worksheet.cell(row=row_num, column=2, value=att.student.group.name if att.student.group else 'Н/Д')
        worksheet.cell(row=row_num, column=3, value=att.subject.subject_name if att.subject else 'Н/Д')
        worksheet.cell(row=row_num, column=4, value=att.date.strftime('%d.%m.%Y'))
        worksheet.cell(row=row_num, column=5, value=att.get_status_display())
        worksheet.cell(row=row_num, column=6, value=att.date.strftime('%d.%m.%Y'))
        worksheet.cell(row=row_num, column=7, value=att.created_by.username if att.created_by else 'Система')
    
    # Statistics sheet
    stats_sheet = workbook.create_sheet("Статистика")
    stats_data = [
        ['Көрсөткүч', 'Мааниси'],
        ['Жалпы жазуулар', attendances.count()],
        ['Катышкандар', attendances.filter(status='Present').count()],
        ['Катышпагандар', attendances.filter(status='Absent').count()],
        ['Кечиккендер', attendances.filter(status='Late').count()],
        ['Уруксат менен жоктор', attendances.filter(status='Excused').count()],
    ]
    
    for row_num, (label, value) in enumerate(stats_data, 1):
        stats_sheet.cell(row=row_num, column=1, value=label)
        stats_sheet.cell(row=row_num, column=2, value=value)
    
    workbook.save(response)
    return response

def export_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    p = canvas.Canvas(response)
    p.drawString(100, 750, "Катышуу Отчету")
    y = 700
    for att in Attendance.objects.all()[:20]:
        p.drawString(100, y, f"{att.student.name} - {att.status} - {att.date}")
        y -= 20
    p.showPage()
    p.save()
    return response

def export_excel(request):
    wb = Workbook()
    ws = wb.active
    ws['A1'] = 'Студент'
    ws['B1'] = 'Сабак'
    ws['C1'] = 'Статус'
    ws['D1'] = 'Дата'
    row = 2
    for att in Attendance.objects.all():
        ws[f'A{row}'] = att.student.name
        ws[f'B{row}'] = att.subject.subject_name if att.subject else 'Н/Д'
        ws[f'C{row}'] = att.status
        ws[f'D{row}'] = str(att.date)
        row += 1
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="report.xlsx"'
    wb.save(response)
    return response

# Жалпы расписание view (ролдорго жараша багыттоо)
@login_required
def schedule(request):
    if request.user.userprofile.role == 'ADMIN' or request.user.userprofile.role == 'MANAGER':
        return redirect('schedule_edit')
    elif request.user.userprofile.role == 'STUDENT':
        return redirect('student_schedule')
    elif request.user.userprofile.role == 'TEACHER':
        return redirect('teacher_attendance')  # Жаңы жоктоо системасына багыттоо
    else:
        messages.error(request, 'Сизде расписаниега кирүү укугу жок.')
        return redirect('dashboard')

# ============= БОШОТУУ СУРАМДАРЫ =============

@login_required
def submit_leave_request(request):
    """Студент бошотуу сурамын жөнөтөт"""
    if request.user.userprofile.role != 'STUDENT':
        messages.error(request, 'Бул функция студенттер үчүн гана.')
        return redirect('dashboard')
    
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Студент профили табылган жок.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.student = student
            leave_request.save()
            
            # Автоматтык билдирме жөнөтүү
            send_leave_request_notification(leave_request)
            
            messages.success(request, 'Бошотуу сурамыңыз ийгиликтүү жөнөтүлдү. Администрацияга билдирме жөнөтүлдү.')
            return redirect('my_leave_requests')
    else:
        form = LeaveRequestForm()
    
    return render(request, 'leave/submit_request.html', {'form': form})

@login_required
def my_leave_requests(request):
    """Студенттин өз бошотуу сурамдарын көрүү"""
    if request.user.userprofile.role != 'STUDENT':
        messages.error(request, 'Бул функция студенттер үчүн гана.')
        return redirect('dashboard')
    
    try:
        student = Student.objects.get(user=request.user)
        leave_requests = LeaveRequest.objects.filter(student=student).order_by('-created_at')
    except Student.DoesNotExist:
        leave_requests = []
        messages.error(request, 'Студент профили табылган жок.')
    
    return render(request, 'leave/my_requests.html', {'leave_requests': leave_requests})

@login_required
@user_passes_test(lambda u: u.userprofile.role in ['ADMIN', 'MANAGER', 'TEACHER'])
def manage_leave_requests(request):
    """Администраторлор/менеджерлер бошотуу сурамдарын башкарат"""
    pending_requests = LeaveRequest.objects.filter(status='PENDING').order_by('-created_at')
    all_requests = LeaveRequest.objects.all().order_by('-created_at')
    
    context = {
        'pending_requests': pending_requests,
        'all_requests': all_requests,
    }
    return render(request, 'leave/manage_requests.html', context)

@login_required
@user_passes_test(lambda u: u.userprofile.role in ['ADMIN', 'MANAGER', 'TEACHER'])
def approve_leave_request(request, request_id):
    """Бошотуу сурамын бекитүү"""
    leave_request = get_object_or_404(LeaveRequest, id=request_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            leave_request.status = 'APPROVED'
            leave_request.approved_by = request.user
            leave_request.save()
            
            # Бекитилген мөөнөтүндө автоматтык "Excused" белгиси коюу
            current_date = leave_request.start_date
            while current_date <= leave_request.end_date:
                # Ошол студенттин ошол күндөгү сабактары үчүн Excused деп белгилөө
                schedules = Schedule.objects.filter(group=leave_request.student.group)
                for schedule in schedules:
                    Attendance.objects.update_or_create(
                        student=leave_request.student,
                        subject=schedule.subject,
                        date=current_date,
                        defaults={
                            'status': 'Excused',
                            'created_by': request.user,
                            'leave_request': leave_request
                        }
                    )
                current_date += timedelta(days=1)
            
            # Билдирме жөнөтүү
            send_leave_decision_notification(leave_request, request.user)
            
            messages.success(request, f'{leave_request.student.name}дын бошотуу сурамы бекитилди. Студентке жана ата-энелерине билдирме жөнөтүлдү.')
        
        elif action == 'reject':
            leave_request.status = 'REJECTED' 
            leave_request.approved_by = request.user
            leave_request.save()
            
            # Билдирме жөнөтүү
            send_leave_decision_notification(leave_request, request.user)
            
            messages.info(request, f'{leave_request.student.name}дын бошотуу сурамы четке кагылды. Студентке жана ата-энелерине билдирме жөнөтүлдү.')
    
    return redirect('manage_leave_requests')

# ============= NOTIFICATION VIEWS =============

@login_required
def notifications(request):
    """Колдонуучунун билдирмелерин көрсөтүү"""
    user_notifications = Notification.objects.filter(recipient=request.user)
    unread_count = user_notifications.filter(is_read=False).count()
    
    return render(request, 'notifications/list.html', {
        'notifications': user_notifications,
        'unread_count': unread_count
    })

@login_required
def mark_notification_read(request, notification_id):
    """Билдирмени окулган деп белгилөө"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('HX-Request'):
        # HTMX request болсо
        return JsonResponse({'success': True})
    
    return redirect('notifications')

@login_required
def mark_all_notifications_read(request):
    """Бардык билдирмелерди окулган деп белгилөө"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'Бардык билдирмелер окулган деп белгиленди.')
    return redirect('notifications')

@login_required
@user_passes_test(lambda u: u.userprofile.role in ['ADMIN', 'MANAGER'])
def send_bulk_notification(request):
    """Көптөгөн колдонуучуларга билдирме жөнөтүү"""
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        recipient_type = request.POST.get('recipient_type')  # all_students, all_parents, specific_group
        group_id = request.POST.get('group_id')
        
        recipients = []
        
        if recipient_type == 'all_students':
            recipients = User.objects.filter(userprofile__role='STUDENT')
        elif recipient_type == 'all_parents':
            recipients = User.objects.filter(userprofile__role='PARENT')
        elif recipient_type == 'specific_group' and group_id:
            recipients = User.objects.filter(
                student__group_id=group_id
            )
        
        # Билдирмелерди түзүү
        notifications_to_create = []
        for recipient in recipients:
            notifications_to_create.append(
                Notification(
                    recipient=recipient,
                    sender=request.user,
                    notification_type='GENERAL',
                    title=title,
                    message=message
                )
            )
        
        # Bulk create для эффективности
        Notification.objects.bulk_create(notifications_to_create)
        
        messages.success(request, f'{len(recipients)} колдонуучуга билдирме жөнөтүлдү.')
        return redirect('notifications')
    
    groups = Group.objects.all()
    return render(request, 'notifications/bulk_send.html', {'groups': groups})

# ============= SCHEDULE MANAGEMENT =============

@login_required
@login_required
def manage_schedule(request):
    """Расписание башкаруу (Админ/Менеджер үчүн)"""
    profile = UserProfile.objects.get(user=request.user)
    
    # Уруксат текшерүү
    if profile.role not in ['ADMIN', 'MANAGER']:
        messages.error(request, 'Сизге бул бетке кирүүгө уруксат жок.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            subject_id = request.POST.get('subject_id')
            group_id = request.POST.get('group_id')
            day = request.POST.get('day')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            
            if not all([subject_id, group_id, day, start_time, end_time]):
                return JsonResponse({'error': 'Бардык талапка сай маалыматты толтуруңуз'}, status=400)
            
            subject = Subject.objects.get(id=subject_id)
            group = Group.objects.get(id=group_id)
            
            # Убакыт кайталануусун текшерүү
            conflict = Schedule.objects.filter(
                group=group,
                day=day,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exists()
            
            if conflict:
                return JsonResponse({'error': 'Бул убакытта группада башка сабак бар'}, status=400)
            
            # Мугалимдин убакыт кайталануусун текшерүү
            teacher_conflict = Schedule.objects.filter(
                subject__teacher=subject.teacher,
                day=day,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exists()
            
            if teacher_conflict:
                return JsonResponse({'error': 'Бул убакытта мугалим башка группада сабак өтөт'}, status=400)
            
            # Жаңы расписание түзүү
            schedule = Schedule.objects.create(
                subject=subject,
                group=group,
                day=day,
                start_time=start_time,
                end_time=end_time
            )
            
            return JsonResponse({'success': True, 'message': 'Сабак ийгиликтүү кошулду'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    # Филтрлер
    course_filter = request.GET.get('course')
    group_filter = request.GET.get('group') 
    teacher_filter = request.GET.get('teacher')
    day_filter = request.GET.get('day')
    
    # Бардык маалыматтар
    courses = Course.objects.all().order_by('year')
    groups = Group.objects.select_related('course').all().order_by('course__year', 'name')
    teachers = Teacher.objects.all().order_by('name')
    subjects = Subject.objects.select_related('teacher', 'course').all()
    
    # Курс боюнча иерархия түзүү
    courses_hierarchy = []
    
    for course in courses:
        course_groups = groups.filter(course=course)
        
        if course_filter and str(course.id) != course_filter:
            continue
            
        groups_data = []
        for group in course_groups:
            if group_filter and str(group.id) != group_filter:
                continue
                
            # Группанын расписаниеси
            schedules = Schedule.objects.filter(group=group).select_related(
                'subject__teacher'
            ).order_by('day', 'start_time')
            
            # Филтрлерди колдонуу
            if teacher_filter:
                schedules = schedules.filter(subject__teacher_id=teacher_filter)
            if day_filter:
                schedules = schedules.filter(day=day_filter)
            
            # Студенттердин саны
            students_count = Student.objects.filter(group=group).count()
            
            groups_data.append({
                'group': group,
                'schedules': schedules,
                'students_count': students_count
            })
        
        if groups_data:  # Эгер группалар бар болсо гана кошуу
            courses_hierarchy.append({
                'course': course,
                'groups': groups_data
            })
    
    context = {
        'courses_hierarchy': courses_hierarchy,
        'courses': courses,
        'groups': groups,
        'all_groups': groups,  # Modal үчүн
        'teachers': teachers,
        'subjects': subjects,
    }
    
    return render(request, 'manage_schedule.html', context)

@login_required 
def delete_schedule(request, schedule_id):
    """Расписание өчүрүү"""
    profile = UserProfile.objects.get(user=request.user)
    
    if profile.role not in ['ADMIN', 'MANAGER']:
        return JsonResponse({'error': 'Уруксат жок'}, status=403)
    
    try:
        schedule = Schedule.objects.get(id=schedule_id)
        schedule.delete()
        return JsonResponse({'success': True, 'message': 'Сабак ийгиликтүү өчүрүлдү'})
    except Schedule.DoesNotExist:
        return JsonResponse({'error': 'Сабак табылган жок'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def manage_subjects(request):
    """Сабактар (Предметтер) көрүү панели"""
    profile = UserProfile.objects.get(user=request.user)
    
    # Уруксат текшерүү - бардык роль кире алат, бирок ADMIN/MANAGER гана өзгөртө алат
    if profile.role not in ['ADMIN', 'MANAGER', 'TEACHER']:
        messages.error(request, 'Сизге бул бетке кирүүгө уруксат жок.')
        return redirect('dashboard')
    
    # Филтрлер
    course_filter = request.GET.get('course')
    teacher_filter = request.GET.get('teacher')
    search = request.GET.get('search', '').strip()
    
    # Негизги маалыматтар
    subjects = Subject.objects.select_related('teacher', 'course').all()
    courses = Course.objects.all().order_by('year')
    teachers = Teacher.objects.all().order_by('name')
    
    # Филтрлерди колдонуу
    if course_filter:
        subjects = subjects.filter(course_id=course_filter)
    if teacher_filter:
        subjects = subjects.filter(teacher_id=teacher_filter)
    if search:
        subjects = subjects.filter(subject_name__icontains=search)
    
    subjects = subjects.order_by('course__year', 'subject_name')
    
    # Статистика эсептөө
    total_subjects = subjects.count()
    subjects_by_course = {}
    subjects_by_teacher = {}
    
    for subject in subjects:
        # Курс боюнча топтоо
        course_name = subject.course.name
        if course_name not in subjects_by_course:
            subjects_by_course[course_name] = []
        subjects_by_course[course_name].append(subject)
        
        # Мугалим боюнча топтоо
        teacher_name = subject.teacher.name if subject.teacher else "Мугалим дайындалган жок"
        if teacher_name not in subjects_by_teacher:
            subjects_by_teacher[teacher_name] = []
        subjects_by_teacher[teacher_name].append(subject)
    
    # Ар бир сабак үчүн кошумча маалымат
    subjects_data = []
    for subject in subjects:
        # Бул сабак боюнча расписание саны
        schedule_count = Schedule.objects.filter(subject=subject).count()
        
        # Бул сабак боюнча студенттердин саны
        students_count = Student.objects.filter(
            group__schedule__subject=subject
        ).distinct().count()
        
        subjects_data.append({
            'subject': subject,
            'schedule_count': schedule_count,
            'students_count': students_count
        })
    
    context = {
        'subjects_data': subjects_data,
        'courses': courses,
        'teachers': teachers,
        'total_subjects': total_subjects,
        'subjects_by_course': subjects_by_course,
        'subjects_by_teacher': subjects_by_teacher,
        'course_filter': course_filter,
        'teacher_filter': teacher_filter,
        'search': search,
        'can_edit': profile.role in ['ADMIN', 'MANAGER']
    }
    
    return render(request, 'manage_subjects.html', context)

@login_required
@login_required
def universal_schedule(request):
    """Универсалдуу расписание көрүү - бардык ролдор үчүн"""
    profile = UserProfile.objects.get(user=request.user)
    
    # Күндөр тизмеси
    days = [
        ('Monday', 'Дүйшөмбү'),
        ('Tuesday', 'Шейшемби'), 
        ('Wednesday', 'Шаршемби'),
        ('Thursday', 'Бейшемби'),
        ('Friday', 'Жума'),
        ('Saturday', 'Ишемби'),
    ]
    
    # Убакыт периоддору
    time_slots = [
        ('08:00', '09:30', '1-пара'),
        ('09:40', '11:10', '2-пара'),
        ('11:30', '13:00', '3-пара'), 
        ('14:00', '15:30', '4-пара'),
        ('15:40', '17:10', '5-пара'),
    ]
    
    # Бардык ролдор расписанияны көрө алат
    schedules_query = Schedule.objects.select_related(
        'subject__teacher', 
        'group__course'
    ).prefetch_related('group__student_set').all()
    
    # Филтрлер
    course_filter = request.GET.get('course')
    group_filter = request.GET.get('group')
    teacher_filter = request.GET.get('teacher')
    
    if course_filter:
        schedules_query = schedules_query.filter(group__course_id=course_filter)
    if group_filter:
        schedules_query = schedules_query.filter(group_id=group_filter)
    if teacher_filter:
        schedules_query = schedules_query.filter(subject__teacher_id=teacher_filter)
    
    # Роль боюнча кошумча фильтр
    if profile.role == 'STUDENT':
        try:
            student = Student.objects.get(user=request.user)
            # Студент өз группасын жана башка группаларды да көрө алат
            if not course_filter and not group_filter:
                # Эгер фильтр коюлбаса, өз группасын көрсөтүү
                schedules_query = schedules_query.filter(group=student.group)
        except Student.DoesNotExist:
            pass
    elif profile.role == 'TEACHER':
        try:
            teacher = Teacher.objects.get(user=request.user)
            # Мугалим өз сабактарын жана башка сабактарды да көрө алат
            if not course_filter and not group_filter and not teacher_filter:
                # Эгер фильтр коюлбаса, өз сабактарын көрсөтүү
                schedules_query = schedules_query.filter(subject__teacher=teacher)
        except Teacher.DoesNotExist:
            pass
    
    schedules = schedules_query.order_by('start_time')
    
    # Таблица үчүн маалыматтарды уюштуруу
    schedule_matrix = {}
    
    for day_code, day_name in days:
        schedule_matrix[day_code] = {}
        for start_time, end_time, period_name in time_slots:
            # Бул күн жана убакыт үчүн сабактарды табуу
            from datetime import datetime
            start_dt = datetime.strptime(start_time, '%H:%M').time()
            end_dt = datetime.strptime(end_time, '%H:%M').time()
            
            day_schedules = schedules.filter(
                day=day_code,
                start_time__lte=end_dt,
                end_time__gte=start_dt
            )
            
            schedule_matrix[day_code][period_name] = {
                'time_range': f"{start_time} - {end_time}",
                'schedules': day_schedules
            }
    
    # Филтр үчүн маалыматтар
    courses = Course.objects.all().order_by('year')
    groups = Group.objects.select_related('course').all().order_by('course__year', 'name')
    teachers = Teacher.objects.all().order_by('name')
    
    # Статистика
    total_schedules = schedules.count()
    unique_groups = schedules.values('group').distinct().count()
    unique_teachers = schedules.values('subject__teacher').distinct().count()
    
    context = {
        'days': days,
        'time_slots': time_slots,
        'schedule_matrix': schedule_matrix,
        'courses': courses,
        'groups': groups,
        'teachers': teachers,
        'course_filter': course_filter,
        'group_filter': group_filter,
        'teacher_filter': teacher_filter,
        'user_role': profile.role,
        'total_schedules': total_schedules,
        'unique_groups': unique_groups,
        'unique_teachers': unique_teachers,
        'show_all': True,  # Бардык маалыматты көрсөтүү
    }
    
    return render(request, 'universal_schedule.html', context)

def weekly_schedule(request):
    """Жумалык расписание таблицасы - ар күн үчүн так сабактар"""
    profile = UserProfile.objects.get(user=request.user)
    
    # Бардык роль үчүн ачык, бирок ар бир роль өз маалыматын көрөт
    
    # Күндөр тизмеси
    days = [
        ('Monday', 'Дүйшөмбү'),
        ('Tuesday', 'Шейшемби'), 
        ('Wednesday', 'Шаршемби'),
        ('Thursday', 'Бейшемби'),
        ('Friday', 'Жума'),
        ('Saturday', 'Ишемби'),
    ]
    
    # Убакыт периоддору
    time_slots = [
        ('08:00', '09:30', '1-пара'),
        ('09:40', '11:10', '2-пара'),
        ('11:30', '13:00', '3-пара'), 
        ('14:00', '15:30', '4-пара'),
        ('15:40', '17:10', '5-пара'),
    ]
    
    # Роль боюнча филтер
    schedules_query = Schedule.objects.select_related('subject__teacher', 'group__course').all()
    
    if profile.role == 'STUDENT':
        try:
            student = Student.objects.get(user=request.user)
            schedules_query = schedules_query.filter(group=student.group)
        except Student.DoesNotExist:
            schedules_query = Schedule.objects.none()
    elif profile.role == 'TEACHER':
        try:
            teacher = Teacher.objects.get(user=request.user)
            schedules_query = schedules_query.filter(subject__teacher=teacher)
        except Teacher.DoesNotExist:
            schedules_query = Schedule.objects.none()
    # MANAGER/ADMIN үчүн бардык расписаниелер көрүнөт
    
    # Филтрлер (MANAGER/ADMIN үчүн)
    course_filter = request.GET.get('course')
    group_filter = request.GET.get('group')
    teacher_filter = request.GET.get('teacher')
    
    if course_filter:
        schedules_query = schedules_query.filter(group__course_id=course_filter)
    if group_filter:
        schedules_query = schedules_query.filter(group_id=group_filter)
    if teacher_filter:
        schedules_query = schedules_query.filter(subject__teacher_id=teacher_filter)
    
    schedules = schedules_query.order_by('start_time')
    
    # Таблица үчүн маалыматтарды уюштуруу
    schedule_matrix = {}
    
    for day_code, day_name in days:
        schedule_matrix[day_code] = {}
        for start_time, end_time, period_name in time_slots:
            # Бул күн жана убакыт үчүн сабактарды табуу
            from datetime import datetime
            start_dt = datetime.strptime(start_time, '%H:%M').time()
            end_dt = datetime.strptime(end_time, '%H:%M').time()
            
            day_schedules = schedules.filter(
                day=day_code,
                start_time__lte=end_dt,
                end_time__gte=start_dt
            )
            
            schedule_matrix[day_code][period_name] = {
                'time_range': f"{start_time} - {end_time}",
                'schedules': day_schedules
            }
    
    # Филтр үчүн маалыматтар
    courses = Course.objects.all().order_by('year') if profile.role in ['ADMIN', 'MANAGER'] else []
    groups = Group.objects.select_related('course').all().order_by('course__year', 'name') if profile.role in ['ADMIN', 'MANAGER'] else []
    teachers = Teacher.objects.all().order_by('name') if profile.role in ['ADMIN', 'MANAGER'] else []
    
    context = {
        'days': days,
        'time_slots': time_slots,
        'schedule_matrix': schedule_matrix,
        'courses': courses,
        'groups': groups,
        'teachers': teachers,
        'course_filter': course_filter,
        'group_filter': group_filter,
        'teacher_filter': teacher_filter,
        'user_role': profile.role,
    }
    
    return render(request, 'weekly_schedule.html', context)