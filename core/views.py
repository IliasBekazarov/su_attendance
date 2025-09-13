from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q, Count
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile, Student, Teacher, Course, Group, Attendance, Notification, Subject, Schedule
from .forms import StudentRegistrationForm, NotificationForm
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from datetime import datetime, date, timedelta
from dal import autocomplete
from django import forms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

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

def user_login(request):
    if request.method == 'POST':
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
def dashboard(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'STUDENT'})
    if created:
        messages.info(request, 'Профилиңиз автоматтык түрдө түзүлдү (STUDENT ролу).')
    role = profile.role
    context = {'role': role}
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if role in ['ADMIN', 'MANAGER', 'TEACHER']:
        total_students = Student.objects.count()
        total_teachers = Teacher.objects.count()
        total_groups = Group.objects.count()
        attendance_stats = Attendance.objects.values('status').annotate(count=Count('status'))
        context.update({
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_groups': total_groups,
            'stats': attendance_stats,
        })
        if role == 'TEACHER':
            teacher = Teacher.objects.get(user=request.user)
            notifications = Notification.objects.filter(teacher=teacher).order_by('-created_at')
            context.update({'notifications': notifications})
    elif role == 'STUDENT':
        student = Student.objects.get_or_create(
            user=request.user,
            defaults={
                'name': request.user.get_full_name() or request.user.username,
                'course': Course.objects.first() or Course.objects.create(name='1st Year', year=1),
                'group': Group.objects.first() or Group.objects.create(name='A-Group', course=Course.objects.first())
            }
        )[0]
        attendance = Attendance.objects.filter(student=student)
        if start_date:
            attendance = attendance.filter(date__gte=start_date)
        if end_date:
            attendance = attendance.filter(date__lte=end_date)
        percentage = (attendance.filter(status='Present').count() / attendance.count() * 100) if attendance.count() > 0 else 0
        present_count = attendance.filter(status='Present').count()
        absent_count = attendance.filter(status='Absent').count()
        late_count = attendance.filter(status='Late').count()
        context.update({
            'student': student,
            'attendance': attendance,
            'percentage': percentage,
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'start_date': start_date,
            'end_date': end_date
        })
    elif role == 'PARENT':
        students = profile.students.all()
        if students:
            students_data = []
            for student in students:
                attendance = Attendance.objects.filter(student=student)
                if start_date:
                    attendance = attendance.filter(date__gte=start_date)
                if end_date:
                    attendance = attendance.filter(date__lte=end_date)
                percentage = (attendance.filter(status='Present').count() / attendance.count() * 100) if attendance.count() > 0 else 0
                present_count = attendance.filter(status='Present').count()
                absent_count = attendance.filter(status='Absent').count()
                late_count = attendance.filter(status='Late').count()
                notifications = Notification.objects.filter(student=student).order_by('-created_at')
                students_data.append({
                    'student': student,
                    'attendance': attendance,
                    'percentage': percentage,
                    'present_count': present_count,
                    'absent_count': absent_count,
                    'late_count': late_count,
                    'notifications': notifications
                })
            context.update({'students_data': students_data, 'start_date': start_date, 'end_date': end_date})
        else:
            messages.error(request, 'Балаңыздын профили байланыштырылган эмес. Администраторго кайрылыңыз.')
            context.update({'message': 'Баланын маалыматы жок'})

    return render(request, 'dashboard.html', context)

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
def schedule_edit(request):
    if request.user.userprofile.role != 'MANAGER':
        messages.error(request, 'Бул функция менеджерлер үчүн гана.')
        return redirect('dashboard')

    schedules = Schedule.objects.all()  # Бардык расписаниелер
    courses = Course.objects.all()
    periods = [
        {'period': i, 'start_time': f'{10 + (i-1)*1.5:02.0f}:00', 'end_time': f'{11.33 + (i-1)*1.5:02.0f}:20'}
        for i in range(1, 6)
    ]

    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('status_') and value:
                try:
                    parts = key.replace('status_', '').split('_')
                    schedule_id, student_id = parts[0], parts[1]
                    schedule = get_object_or_404(Schedule, id=schedule_id)
                    student = get_object_or_404(Student, id=student_id)
                    Attendance.objects.update_or_create(
                        student=student,
                        schedule=schedule,
                        date=date.today(),
                        defaults={'status': value, 'created_by': request.user}
                    )
                except (IndexError, ValueError):
                    messages.error(request, 'Катышууну сактоодо ката кетти.')
                    continue
        messages.success(request, 'Катышуу сакталды.')
        return redirect('schedule_edit')

    context = {
        'courses': courses,
        'active_course': courses.first() if courses.exists() else None,
        'periods': periods,
        'schedules': schedules,
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
    if request.user.userprofile.role != 'TEACHER':
        messages.error(request, 'Бул функция мугалимдер үчүн гана.')
        return redirect('dashboard')
    
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, 'Сиз мугалим катары катталган эмессиз.')
        return redirect('dashboard')

    # Мугалимдин сабактары гана чыгарылат
    schedules = Schedule.objects.filter(subject__teacher=teacher)
    courses = Course.objects.all()
    periods = [
        {'period': i, 'start_time': f'{10 + (i-1)*1.5:02.0f}:00', 'end_time': f'{11.33 + (i-1)*1.5:02.0f}:20'}
        for i in range(1, 6)
    ]

    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('status_') and value:
                try:
                    parts = key.replace('status_', '').split('_')
                    schedule_id, student_id = parts[0], parts[1]
                    schedule = get_object_or_404(Schedule, id=schedule_id)
                    student = get_object_or_404(Student, id=student_id)
                    Attendance.objects.update_or_create(
                        student=student,
                        schedule=schedule,
                        date=date.today(),
                        defaults={'status': value, 'created_by': request.user}
                    )
                except (IndexError, ValueError):
                    messages.error(request, 'Катышууну сактоодо ката кетти.')
                    continue
        messages.success(request, 'Катышуу сакталды.')
        return redirect('teacher_schedule')

    context = {
        'courses': courses,
        'active_course': courses.first() if courses.exists() else None,
        'periods': periods,
        'schedules': schedules,
    }
    return render(request, 'teacher_schedule.html', context)
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
    if request.method == 'POST':
        format_type = request.POST.get('format')
        if format_type == 'pdf':
            return export_pdf(request)
        elif format_type == 'excel':
            return export_excel(request)
    attendances = Attendance.objects.all()
    context = {'attendances': attendances}
    return render(request, 'report.html', context)

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
        return redirect('teacher_schedule')
    else:
        messages.error(request, 'Сизде расписаниега кирүү укугу жок.')
        return redirect('dashboard')