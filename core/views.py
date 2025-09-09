from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q, Count
from .models import Student, Subject, Attendance, UserProfile, Course, Group, Teacher
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from django.core.mail import send_mail
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.models import User

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.get_or_create(user=user, defaults={'role': 'STUDENT'})
            messages.success(request, 'Аккаунт түзүлдү!')
            return redirect('login')
    else:
        form = UserCreationForm()
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

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import UserProfile, Student, Teacher, Attendance, Group, Course
from django.db.models import Count

@login_required
def dashboard(request):
    # UserProfile түзүү же алуу
    profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'role': 'STUDENT'}
    )
    if created:
        messages.warning(request, 'Профилиңиз автоматтык түрдө түзүлдү (STUDENT ролу). Администраторго кайрылыңыз.')

    role = profile.role
    context = {'role': role}

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
    elif role == 'STUDENT':
        try:
            student = Student.objects.get(user=request.user)
            attendance = Attendance.objects.filter(student=student)
            percentage = (attendance.filter(status='Present').count() / attendance.count() * 100) if attendance.count() > 0 else 0
            context.update({'student': student, 'attendance': attendance, 'percentage': percentage})
        except Student.DoesNotExist:
            # Студент профили жок болсо, түзүү
            default_course = Course.objects.first()  # Демейки курс
            default_group = Group.objects.first()  # Демейки топ
            student = Student.objects.create(
                user=request.user,
                name=request.user.get_full_name() or request.user.username,
                course=default_course,
                group=default_group
            )
            messages.info(request, 'Студент профилиңиз автоматтык түрдө түзүлдү.')
            attendance = Attendance.objects.filter(student=student)
            percentage = (attendance.filter(status='Present').count() / attendance.count() * 100) if attendance.count() > 0 else 0
            context.update({'student': student, 'attendance': attendance, 'percentage': percentage})
    elif role == 'PARENT':
        if profile.student:
            student = profile.student
            attendance = Attendance.objects.filter(student=student)
            percentage = (attendance.filter(status='Present').count() / attendance.count() * 100) if attendance.count() > 0 else 0
            context.update({'student': student, 'attendance': attendance, 'percentage': percentage})
        else:
            messages.info(request, 'Сиздин балаңыздын профили жок. Администраторго кайрылыңыз.')
            context.update({'message': 'Баланыңыздын маалыматы жок'})
    return render(request, 'dashboard.html', context)

@login_required
def schedule(request):
    try:
        profile = request.user.userprofile
    except User.userprofile.RelatedObjectDoesNotExist:
        # Эгер профиль жок болсо, демейки рол менен түзүү же ката билдирүүсүн көрсөтүү
        profile = UserProfile.objects.create(user=request.user, role='STUDENT')
        messages.warning(request, 'Профилиңиз автоматтык түрдө түзүлдү (STUDENT ролу). Администраторго кайрылыңыз.')

    role = profile.role
    if request.method == 'POST' and role in ['ADMIN', 'MANAGER']:
        subject_name = request.POST.get('subject_name')
        teacher_id = request.POST.get('teacher_id')
        course_id = request.POST.get('course_id')
        Subject.objects.create(
            subject_name=subject_name,
            teacher=Teacher.objects.get(id=teacher_id) if teacher_id else None,
            course=Course.objects.get(id=course_id) if course_id else None
        )
        messages.success(request, 'Сабак кошулду!')
        return redirect('schedule')
    subjects = Subject.objects.all()
    if role == 'TEACHER':
        try:
            teacher = Teacher.objects.get(user=request.user)
            subjects = subjects.filter(teacher=teacher)
        except Teacher.DoesNotExist:
            subjects = Subject.objects.none()
            messages.info(request, 'Сиздин мугалим профилиңиз жок. Администраторго кайрылыңыз.')
    context = {'subjects': subjects, 'role': role, 'teachers': Teacher.objects.all(), 'courses': Course.objects.all()}
    return render(request, 'schedule.html', context)

@login_required
@user_passes_test(is_teacher)
def mark_attendance(request, subject_id):
    if request.method == 'POST':
        subject = Subject.objects.get(id=subject_id)
        for key, value in request.POST.items():
            if key.startswith('status_'):
                student_id = int(key.split('_')[1])
                Attendance.objects.create(
                    student_id=student_id,
                    subject=subject,
                    date=datetime.now().date(),
                    status=value,
                    created_by=request.user
                )
        messages.success(request, 'Катышуу белгиленди!')
        return redirect('schedule')
    subject = Subject.objects.get(id=subject_id)
    students = Student.objects.filter(course=subject.course)
    return render(request, 'timetable.html', {'students': students, 'subject': subject})

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
        ws[f'B{row}'] = att.subject.subject_name
        ws[f'C{row}'] = att.status
        ws[f'D{row}'] = str(att.date)
        row += 1
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="report.xlsx"'
    wb.save(response)
    return response