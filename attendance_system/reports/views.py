from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from attendance.models import AttendanceRecord
from accounts.permissions import IsTeacherOrAdmin
from datetime import timedelta
from django.utils import timezone
from django.http import HttpResponse
import csv
from reportlab.pdfgen import canvas

class ReportView(APIView):
    permission_classes = [IsTeacherOrAdmin]

    def get(self, request, report_type):
        now = timezone.now()
        if report_type == 'daily':
            start = now - timedelta(days=1)
        elif report_type == 'weekly':
            start = now - timedelta(weeks=1)
        elif report_type == 'monthly':
            start = now - timedelta(days=30)
        else:
            return Response({'error': 'Invalid report type'}, status=400)

        queryset = AttendanceRecord.objects.filter(date__gte=start)
        if request.user.role == 'teacher':
            queryset = queryset.filter(teacher=request.user)

        data = queryset.values('status').annotate(count=Count('status'))
        return Response(data)

class ExportReportView(APIView):
    permission_classes = [IsTeacherOrAdmin]

    def get(self, request, format):
        if format not in ['csv', 'pdf']:
            return Response({'error': 'Invalid format'}, status=400)

        # Example: Generate all attendance data
        queryset = AttendanceRecord.objects.all()
        if request.user.role == 'teacher':
            queryset = queryset.filter(teacher=request.user)

        if format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="report.csv"'
            writer = csv.writer(response)
            writer.writerow(['ID', 'Student', 'Status', 'Date'])
            for record in queryset:
                writer.writerow([record.id, record.student.username, record.status, record.date])
            return response

        elif format == 'pdf':
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="report.pdf"'
            p = canvas.Canvas(response)
            p.drawString(100, 800, "Attendance Report")
            y = 780
            for record in queryset:
                p.drawString(100, y, f"{record.student.username}: {record.status} on {record.date}")
                y -= 20
            p.save()
            return response