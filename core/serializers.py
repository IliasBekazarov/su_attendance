from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserProfile, Student, Teacher, Course, Group, Subject, 
    Schedule, Attendance, LeaveRequest, Notification
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['date_joined']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'role']

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name', 'year']

class GroupSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    course_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'course', 'course_id']

class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    group = GroupSerializer(read_only=True)
    
    class Meta:
        model = Student
        fields = ['id', 'name', 'user', 'course', 'group']

class TeacherSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Teacher
        fields = ['id', 'name', 'user']

class SubjectSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    
    class Meta:
        model = Subject
        fields = ['id', 'subject_name', 'teacher', 'course']

class ScheduleSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    group = GroupSerializer(read_only=True)
    
    class Meta:
        model = Schedule
        fields = ['id', 'subject', 'group', 'day', 'start_time', 'end_time']

class AttendanceSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    schedule = ScheduleSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Attendance
        fields = ['id', 'student', 'subject', 'schedule', 'date', 'status', 'created_by']

class AttendanceCreateSerializer(serializers.ModelSerializer):
    """Катышууну жазуу үчүн serializer"""
    class Meta:
        model = Attendance
        fields = ['student', 'subject', 'schedule', 'date', 'status']

class LeaveRequestSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    
    class Meta:
        model = LeaveRequest
        fields = [
            'id', 'student', 'leave_type', 'start_date', 'end_date', 
            'reason', 'status', 'approved_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['approved_by', 'created_at', 'updated_at']

class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    """Бошотуу сурамын түзүү үчүн serializer"""
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']

class NotificationSerializer(serializers.ModelSerializer):
    recipient = UserSerializer(read_only=True)
    sender = UserSerializer(read_only=True)
    student = StudentSerializer(read_only=True)
    leave_request = LeaveRequestSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'recipient', 'sender', 'notification_type', 'title', 
            'message', 'created_at', 'is_read', 'student', 'leave_request'
        ]
        read_only_fields = ['sender', 'created_at']

# ============= СТАТИСТИКА СЕРИАЛАЙЗЕРЛЕРИ =============

class AttendanceStatsSerializer(serializers.Serializer):
    """Катышуу статистикасы үчүн"""
    total_records = serializers.IntegerField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    late_count = serializers.IntegerField()
    excused_count = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()

class GroupStatsSerializer(serializers.Serializer):
    """Группа статистикасы үчүн"""
    group_name = serializers.CharField()
    total_students = serializers.IntegerField()
    total_records = serializers.IntegerField()
    present_count = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()
