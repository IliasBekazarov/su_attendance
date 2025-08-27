from django.urls import path
from .views import GroupListCreateView, GroupDetailView, ScheduleListCreateView, ScheduleDetailView

urlpatterns = [
    path('groups/', GroupListCreateView.as_view(), name='group-list'),
    path('groups/<int:pk>/', GroupDetailView.as_view(), name='group-detail'),
    path('schedule/', ScheduleListCreateView.as_view(), name='schedule-list'),
    path('schedule/<int:pk>/', ScheduleDetailView.as_view(), name='schedule-detail'),
]