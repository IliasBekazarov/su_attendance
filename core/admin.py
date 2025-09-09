from django.contrib import admin
from .models import UserProfile, Course, Group, Teacher, Student, Subject, Attendance

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'student')
    list_filter = ('role',)
    search_fields = ('user__username',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'year')
    search_fields = ('name',)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'course')
    list_filter = ('course',)
    search_fields = ('name',)

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    search_fields = ('name', 'user__username')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'course', 'user', 'created_at')
    list_filter = ('group', 'course')
    search_fields = ('name', 'user__username')

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_name', 'teacher', 'course', 'created_at')
    list_filter = ('course', 'teacher')
    search_fields = ('subject_name',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'date', 'status', 'created_by')
    list_filter = ('status', 'date', 'subject')
    search_fields = ('student__name', 'subject__subject_name')