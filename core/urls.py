from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
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
    path('schedule/mark/<int:schedule_id>/', views.mark_group_attendance, name='mark_group_attendance'),
    path('notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('schedule/mark/<int:group_id>/<int:period>/', views.mark_schedule_attendance, name='mark_schedule_attendance'),
    path('schedule/mark/submit/', views.submit_schedule_attendance, name='submit_schedule_attendance'),
]