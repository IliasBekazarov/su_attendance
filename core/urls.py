from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('schedule/', views.schedule, name='schedule'),
    path('mark_attendance/<int:subject_id>/', views.mark_attendance, name='mark_attendance'),
    path('report/', views.report, name='report'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('logout/', views.user_logout, name='logout'),  # user_logout менен
]