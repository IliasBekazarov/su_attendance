# attendance/views.py (excerpt)
from django.core.mail import send_mail
from rest_framework import generics
from . import AttendanceRecord
from .serializers import AttendanceSerializer
from accounts.permissions import IsTeacher

class AttendanceListCreateView(generics.ListCreateAPIView):
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsTeacher]

    def perform_create(self, serializer):
        instance = serializer.save(teacher=self.request.user)
        if instance.status in ('absent', 'late'):
            parent = instance.student.student_profile.parent
            if parent:
                send_mail(
                    'Attendance Alert',
                    f"Your child {instance.student.username} was {instance.status} on {instance.date}.",
                    'from@example.com',
                    [parent.email]
                )