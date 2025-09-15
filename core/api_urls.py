from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .api_views import (
    StudentViewSet, AttendanceViewSet, LeaveRequestViewSet,
    NotificationViewSet, CourseViewSet, GroupViewSet,
    SubjectViewSet, ScheduleViewSet
)

# API Router
router = DefaultRouter()
router.register(r'students', StudentViewSet)
router.register(r'attendance', AttendanceViewSet)
router.register(r'leave-requests', LeaveRequestViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'schedules', ScheduleViewSet)

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    
    # Token Authentication
    path('auth/token/', obtain_auth_token, name='api_token_auth'),
    
    # API Auth (login/logout for browsable API)
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]
