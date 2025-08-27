from django.contrib import admin
from .models import CustomUser, StudentProfile, TeacherProfile, ParentProfile, ManagerProfile  # Added ManagerProfile

admin.site.register(CustomUser)
admin.site.register(StudentProfile)
admin.site.register(TeacherProfile)
admin.site.register(ParentProfile)
admin.site.register(ManagerProfile)  