from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import UserSerializer, RegisterSerializer, StudentProfileSerializer
from .models import CustomUser, StudentProfile
from .permissions import IsAdmin, IsStudent, IsAdminOrManager
from rest_framework.views import APIView
from schedule.models import Group  # Import Group

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

class UserListView(generics.ListCreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class StudentProfileView(generics.RetrieveUpdateAPIView):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [IsStudent]

    def get_object(self):
        return self.request.user.student_profile
    
class AssignGroupView(APIView):
    permission_classes = [IsAdminOrManager]

    def post(self, request):
        student_id = request.data.get('student_id')
        group_id = request.data.get('group_id')
        try:
            student = CustomUser.objects.get(id=student_id, role='student')
            group = Group.objects.get(id=group_id)
            student.student_profile.group = group
            student.student_profile.save()
            return Response({'success': True}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Student not found'}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)