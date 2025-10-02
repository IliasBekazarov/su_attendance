from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from datetime import date, timedelta
from django.shortcuts import get_object_or_404

from .models import (
    UserProfile, Student, Teacher, Course, Group, Subject,
    Schedule, Attendance, LeaveRequest, Notification
)
from .serializers import (
    UserProfileSerializer, StudentSerializer, TeacherSerializer,
    CourseSerializer, GroupSerializer, SubjectSerializer,
    ScheduleSerializer, AttendanceSerializer, AttendanceCreateSerializer,
    LeaveRequestSerializer, LeaveRequestCreateSerializer,
    NotificationSerializer, AttendanceStatsSerializer, GroupStatsSerializer
)

class RoleBasedPermission(permissions.BasePermission):
    """Ролго негизделген кирүү укуктары"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return hasattr(request.user, 'userprofile')

class AdminOrManagerPermission(permissions.BasePermission):
    """Админ же менеджер укугу"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        try:
            return request.user.userprofile.role in ['ADMIN', 'MANAGER']
        except:
            return False

class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    """Студенттер API"""
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    
    def get_queryset(self):
        """Ролго жараша фильтр"""
        user = self.request.user
        if user.userprofile.role == 'STUDENT':
            # Студент өзүн гана көрө алат
            return Student.objects.filter(user=user)
        elif user.userprofile.role == 'PARENT':
            # Ата-энелер өз балдарын көрө алат
            return user.userprofile.students.all()
        else:
            # Админ, менеджер, мугалим бардыгын көрө алат
            return Student.objects.all()

class AttendanceViewSet(viewsets.ModelViewSet):
    """Катышуу API"""
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AttendanceCreateSerializer
        return AttendanceSerializer
    
    def get_queryset(self):
        """Ролго жараша фильтр"""
        user = self.request.user
        queryset = Attendance.objects.all()
        
        if user.userprofile.role == 'STUDENT':
            try:
                student = Student.objects.get(user=user)
                queryset = queryset.filter(student=student)
            except Student.DoesNotExist:
                queryset = Attendance.objects.none()
        elif user.userprofile.role == 'PARENT':
            # Ата-энелер өз балдарынын катышуусун көрө алат
            student_ids = user.userprofile.students.values_list('id', flat=True)
            queryset = queryset.filter(student_id__in=student_ids)
        
        # Дата фильтри
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.order_by('-date')
    
    def perform_create(self, serializer):
        """Катышууну жазганда created_by көрсөтүү"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Катышуу статистикасы"""
        queryset = self.get_queryset()
        
        total_records = queryset.count()
        present_count = queryset.filter(status='Present').count()
        absent_count = queryset.filter(status='Absent').count()
        late_count = queryset.filter(status='Late').count()
        excused_count = queryset.filter(status='Excused').count()
        
        attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0
        
        stats_data = {
            'total_records': total_records,
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'excused_count': excused_count,
            'attendance_percentage': round(attendance_percentage, 2)
        }
        
        serializer = AttendanceStatsSerializer(stats_data)
        return Response(serializer.data)

class LeaveRequestViewSet(viewsets.ModelViewSet):
    """Бошотуу сурамдары API"""
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LeaveRequestCreateSerializer
        return LeaveRequestSerializer
    
    def get_queryset(self):
        """Ролго жараша фильтр"""
        user = self.request.user
        queryset = LeaveRequest.objects.all()
        
        if user.userprofile.role == 'STUDENT':
            try:
                student = Student.objects.get(user=user)
                queryset = queryset.filter(student=student)
            except Student.DoesNotExist:
                queryset = LeaveRequest.objects.none()
        elif user.userprofile.role == 'PARENT':
            # Ата-энелер өз балдарынын сурамдарын көрө алат
            student_ids = user.userprofile.students.values_list('id', flat=True)
            queryset = queryset.filter(student_id__in=student_ids)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Бошотуу сурамын түзгөндө студентти автоматтык көрсөтүү"""
        if self.request.user.userprofile.role == 'STUDENT':
            try:
                student = Student.objects.get(user=self.request.user)
                serializer.save(student=student)
            except Student.DoesNotExist:
                raise serializers.ValidationError("Студент профили табылган жок")
        else:
            raise serializers.ValidationError("Бул функция студенттер үчүн гана")
    
    @action(detail=True, methods=['post'], permission_classes=[AdminOrManagerPermission])
    def approve(self, request, pk=None):
        """Бошотуу сурамын бекитүү"""
        leave_request = self.get_object()
        leave_request.status = 'APPROVED'
        leave_request.approved_by = request.user
        leave_request.save()
        
        # Билдирме жөнөтүү логикасы кошулушу мүмкүн
        
        serializer = self.get_serializer(leave_request)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[AdminOrManagerPermission])
    def reject(self, request, pk=None):
        """Бошотуу сурамын четке кагуу"""
        leave_request = self.get_object()
        leave_request.status = 'REJECTED'
        leave_request.approved_by = request.user
        leave_request.save()
        
        # Билдирме жөнөтүү логикасы кошулушу мүмкүн
        
        serializer = self.get_serializer(leave_request)
        return Response(serializer.data)

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Билдирмелер API"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Колдонуучунун өз билдирмелери"""
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Билдирмени окулган деп белгилөө"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Бардык билдирмелерди окулган деп белгилөө"""
        updated = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).update(is_read=True)
        
        return Response({'updated': updated})

# ============= READ-ONLY VIEWSETS =============

class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """Курстар API (окуу гана)"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]

class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """Группалар API (окуу гана)"""
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Группанын статистикасы"""
        group = self.get_object()
        attendances = Attendance.objects.filter(student__group=group)
        
        total_students = Student.objects.filter(group=group).count()
        total_records = attendances.count()
        present_count = attendances.filter(status='Present').count()
        attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0
        
        stats_data = {
            'group_name': group.name,
            'total_students': total_students,
            'total_records': total_records,
            'present_count': present_count,
            'attendance_percentage': round(attendance_percentage, 2)
        }
        
        serializer = GroupStatsSerializer(stats_data)
        return Response(serializer.data)

class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """Сабактар API (окуу гана)"""
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]

class ScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    """Расписание API (окуу гана)"""
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated, RoleBasedPermission]
