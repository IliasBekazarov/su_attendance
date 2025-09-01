from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, StudentProfile, TeacherProfile, ParentProfile, ManagerProfile

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'role', 'is_active']
    list_filter = ['role', 'is_active']
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'is_active', 'is_staff', 'is_superuser'),
        }),
    )
    search_fields = ['username', 'email']
    ordering = ['username']

    def save_model(self, request, obj, form, change):
        if not change:  # Жаңы колдонуучу кошулганда
            obj.set_password(form.cleaned_data['password1'])
        elif form.cleaned_data.get('password1'):  # Пароль өзгөртүлгөндө
            obj.set_password(form.cleaned_data['password1'])
        super().save_model(request, obj, form, change)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(StudentProfile)
admin.site.register(TeacherProfile)
admin.site.register(ParentProfile)
admin.site.register(ManagerProfile)