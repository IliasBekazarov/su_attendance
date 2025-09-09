from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Student, Teacher

class RegisterForm(forms.ModelForm):
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES)
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Паролду кайталаңыз")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Паролдор дал келбейт.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            
            # UserProfile түзүү
            role = self.cleaned_data.get('role')
            profile = UserProfile.objects.create(user=user, role=role)
            
            # Студент же Мугалим профилин түзүү
            if role == 'STUDENT':
                Student.objects.create(user=user)
            elif role == 'TEACHER':
                Teacher.objects.create(user=user)
                
        return user
