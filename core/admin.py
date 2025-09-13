from django.contrib import admin
from .models import UserProfile, Student, Teacher, Course, Group, Attendance, Subject, Notification

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'get_students']
    list_filter = ['role']
    search_fields = ['user__username']

    def get_students(self, obj):
        return ", ".join([student.name for student in obj.students.all()])
    get_students.short_description = 'Студенттер'

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'course', 'group', 'get_parents']
    list_filter = ['course', 'group']
    search_fields = ['name', 'user__username']

    def get_parents(self, obj):
        return ", ".join([parent.user.username for parent in obj.parents.all()])
    get_parents.short_description = 'Ата-энелер'

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['name', 'user']
    search_fields = ['name', 'user__username']

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['subject_name', 'teacher', 'course']
    list_filter = ['course']
    search_fields = ['subject_name']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'date', 'status', 'created_by']
    list_filter = ['status', 'date']
    search_fields = ['student__name', 'subject__subject_name', 'created_by__username']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'student', 'message', 'created_at', 'is_read']
    list_filter = ['is_read', 'created_at']
    search_fields = ['student__name', 'teacher__name', 'message']

admin.site.register(Course)
admin.site.register(Group)