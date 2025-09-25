from django.contrib import admin
from .models import UserProfile, Student, Teacher, Course, Group, Attendance, Subject, Notification, Schedule, LeaveRequest, TimeSlot

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
    list_display = ['name', 'user', 'degree', 'department']
    list_filter = ['degree', 'department']
    search_fields = ['name', 'user__username', 'department']

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['subject_name', 'teacher', 'course']
    list_filter = ['course']
    search_fields = ['subject_name']

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['get_subject_name', 'get_teacher_name', 'group', 'day', 'start_time', 'end_time', 'room', 'get_student_count']
    list_filter = ['day', 'subject__teacher', 'group__course', 'start_time']
    search_fields = ['subject__subject_name', 'group__name', 'subject__teacher__name', 'room']
    list_per_page = 20
    ordering = ['day', 'start_time', 'group__name']
    
    # Бардык fields кө рсөтүү form да
    fieldsets = (
        ('Негизги маалыматтар', {
            'fields': ('subject', 'group', 'day', 'room')
        }),
        ('Убакыт маалыматтары', {
            'fields': ('start_time', 'end_time'),
            'classes': ('wide',)
        }),
    )
    
    def get_subject_name(self, obj):
        return obj.subject.subject_name
    get_subject_name.short_description = 'Сабак'
    get_subject_name.admin_order_field = 'subject__subject_name'
    
    def get_teacher_name(self, obj):
        return obj.subject.teacher.name if obj.subject.teacher else 'Мугалим жок'
    get_teacher_name.short_description = 'Мугалим'
    get_teacher_name.admin_order_field = 'subject__teacher__name'
    
    def get_student_count(self, obj):
        return obj.group.student_set.count()
    get_student_count.short_description = 'Студенттер саны'
    
    # Фильтрлерди кошуу
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({
            'title': 'Расписание башкаруу - Салымбеков Университети'
        })
        return super().changelist_view(request, extra_context)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'date', 'status', 'created_by', 'leave_request']
    list_filter = ['status', 'date']
    search_fields = ['student__name', 'subject__subject_name', 'created_by__username']

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['student', 'leave_type', 'start_date', 'end_date', 'status', 'approved_by', 'created_at']
    list_filter = ['status', 'leave_type', 'created_at']
    search_fields = ['student__name', 'reason']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'sender', 'notification_type', 'title', 'created_at', 'is_read']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__username', 'sender__username', 'title', 'message']

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_time', 'end_time']
    ordering = ['start_time']
    search_fields = ['name']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'year', 'faculty']
    list_filter = ['year', 'faculty']
    search_fields = ['name', 'faculty']

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'capacity']
    list_filter = ['course']
    search_fields = ['name']