from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import Group, Schedule
from .serializers import GroupSerializer, ScheduleSerializer
from accounts.permissions import IsAdminOrManager

class GroupListCreateView(generics.ListCreateAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdminOrManager]

class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdminOrManager]

class ScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ('admin', 'manager'):
            return Schedule.objects.all()
        elif user.role == 'teacher':
            return Schedule.objects.filter(teacher=user)
        elif user.role == 'student':
            if hasattr(user, 'student_profile') and user.student_profile.group:
                return Schedule.objects.filter(group=user.student_profile.group)
            return Schedule.objects.none()
        elif user.role == 'parent':
            # Assuming one child; adjust if multiple
            child = user.children.first()
            if child and hasattr(child, 'student_profile') and child.student_profile.group:
                return Schedule.objects.filter(group=child.student_profile.group)
            return Schedule.objects.none()
        return Schedule.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role not in ('admin', 'manager'):
            raise PermissionDenied("Only Admin or Manager can create schedules.")
        serializer.save()

class ScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ScheduleSerializer

    def get_queryset(self):
        # Same filtering as list for security
        user = self.request.user
        if user.role in ('admin', 'manager'):
            return Schedule.objects.all()
        elif user.role == 'teacher':
            return Schedule.objects.filter(teacher=user)
        elif user.role == 'student':
            if hasattr(user, 'student_profile') and user.student_profile.group:
                return Schedule.objects.filter(group=user.student_profile.group)
            return Schedule.objects.none()
        elif user.role == 'parent':
            child = user.children.first()
            if child and hasattr(child, 'student_profile') and child.student_profile.group:
                return Schedule.objects.filter(group=child.student_profile.group)
            return Schedule.objects.none()
        return Schedule.objects.none()

    def get_permissions(self):
        if self.request.method in ('GET',):
            return [IsAuthenticated()]
        return [IsAdminOrManager()]