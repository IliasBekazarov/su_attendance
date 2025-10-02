from django.urls import path
from . import views
from . import schedule_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('settings/', views.settings, name='settings'),
    path('schedule/', views.schedule, name='schedule'),
    path('report/', views.report, name='report'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('logout/', views.user_logout, name='logout'),
    path('send-notification/', views.send_notification, name='send_notification'),
    path('schedule/edit/', views.schedule_edit, name='schedule_edit'),
    path('schedule/update/', views.schedule_update, name='schedule_update'),
    path('schedule/student/', views.student_schedule, name='student_schedule'),
    path('schedule/teacher/', views.teacher_schedule, name='teacher_schedule'),
    path('teacher/attendance/', views.teacher_attendance, name='teacher_attendance'),
    path('schedule/mark/<int:schedule_id>/', views.mark_group_attendance, name='mark_group_attendance'),
    path('notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('schedule/mark/<int:group_id>/<int:period>/', views.mark_schedule_attendance, name='mark_schedule_attendance'),
    path('schedule/mark/submit/', views.submit_schedule_attendance, name='submit_schedule_attendance'),
    
    # Жаңы unified schedule системасы
    path('schedule/unified/', schedule_views.unified_schedule, name='unified_schedule'),
    path('api/schedule/data/', schedule_views.get_schedule_data, name='get_schedule_data'),
    path('api/schedule/groups/', schedule_views.get_groups_for_course, name='get_groups_for_course'),
    path('api/schedule/save/', schedule_views.save_schedule_lesson, name='save_schedule_lesson'),
    path('api/schedule/delete/', schedule_views.delete_schedule_lesson, name='delete_schedule_lesson'),
    path('api/schedule/students/', schedule_views.get_lesson_students, name='get_lesson_students'),
    path('api/attendance/save/', schedule_views.save_attendance, name='save_attendance'),
    
    # Бошотуу сурамдары
    path('leave/request/', views.submit_leave_request, name='submit_leave_request'),
    path('leave/my-requests/', views.my_leave_requests, name='my_leave_requests'),
    path('leave/manage/', views.manage_leave_requests, name='manage_leave_requests'),
    path('leave/approve/<int:request_id>/', views.approve_leave_request, name='approve_leave_request'),
    
    # Билдирмелер
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('notifications/bulk-send/', views.send_bulk_notification, name='send_bulk_notification'),
    
    # Расписание башкаруу
    path('manage-schedule/', views.manage_schedule, name='manage_schedule'),
    path('schedule/delete/<int:schedule_id>/', views.delete_schedule, name='delete_schedule'),
    
    # Сабактар башкаруу
    path('manage-subjects/', views.manage_subjects, name='manage_subjects'),
    
    # Жумалык расписание
    path('weekly-schedule/', views.weekly_schedule, name='weekly_schedule'),
    
    # Универсалдуу расписание
    path('universal-schedule/', views.universal_schedule, name='universal_schedule'),
    
    # Студенттик катышуу белгилөө
    path('student/attendance/mark/<int:schedule_id>/', views.mark_student_attendance, name='mark_student_attendance'),
    
    # ПРОФИЛ БАШКАРУУ
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/photo/delete/', views.profile_photo_delete, name='profile_photo_delete'),
    path('profile/completion-check/', views.profile_completion_check, name='profile_completion_check'),
]   