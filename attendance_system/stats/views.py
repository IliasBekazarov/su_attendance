from rest_framework.decorators import api_view
from rest_framework.response import Response
from accounts.models import CustomUser
from schedule.models import Schedule
from attendance.models import AttendanceRecord
from django.utils import timezone
from datetime import timedelta

@api_view(['GET'])
def dashboard_stats(request):
    period = request.query_params.get('period', 'all')
    now = timezone.now()
    if period == 'monthly':
        start = now - timedelta(days=30)
    else:
        start = None

    total_students = CustomUser.objects.filter(groups__name='student').count()
    total_teachers = CustomUser.objects.filter(groups__name='teacher').count()
    total_classes = Schedule.objects.count()
    total_schedules = total_classes
    attendance_records = AttendanceRecord.objects.all() if not start else AttendanceRecord.objects.filter(date__gte=start)
    total_attendance = attendance_records.count()
    present_count = attendance_records.filter(status='present').count()

    trend_data = {}
    for record in attendance_records:
        date_str = record.date.strftime('%Y-%m-%d')
        if date_str not in trend_data:
            trend_data[date_str] = {'present': 0, 'total': 0}
        trend_data[date_str]['total'] += 1
        if record.status == 'present':
            trend_data[date_str]['present'] += 1

    trend = [{'date': date, 'attendance': (data['present'] * 100 // data['total']) if data['total'] else 0} for date, data in trend_data.items()]

    stats = {
        'students': total_students,
        'teachers': total_teachers,
        'classes': total_classes,
        'attendance': (present_count * 100 // total_attendance) if total_attendance else 0,
        'schedules': total_schedules,
        'notifications': 0,
        'trend': trend,
    }
    return Response(stats)