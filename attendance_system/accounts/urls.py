from django.urls import path
from .views import AssignGroupView, RegisterView, UserListView, UserDetailView, ProfileView, StudentProfileView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('student-profile/', StudentProfileView.as_view(), name='student-profile'),
    path('assign-group/', AssignGroupView.as_view(), name='assign-group'),  
]