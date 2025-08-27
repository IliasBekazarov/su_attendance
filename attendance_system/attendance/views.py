from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import AttendanceRecord
from .serializers import AttendanceSerializer
from accounts.permissions import IsTeacher, IsStudentOrParentOrAdmin, IsTeacherOrAdmin

class AttendanceListCreateView(generics.ListCreateAPIView):
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsTeacher()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.role == 'student':
            return AttendanceRecord.objects.filter(student=user)
        elif user.role == 'parent':
            return AttendanceRecord.objects.filter(student__student_profile__parent=user)
        elif user.role == 'teacher':
            return AttendanceRecord.objects.filter(teacher=user)
        elif user.role == 'admin':
            return AttendanceRecord.objects.all()
        return AttendanceRecord.objects.none()

class AttendanceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AttendanceRecord.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsTeacherOrAdmin]