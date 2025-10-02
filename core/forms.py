from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Student, Course, Group, Notification, Schedule, LeaveRequest
from django import forms
from .models import Subject, Group
from django.core.exceptions import ValidationError
import re


class UserProfileForm(forms.ModelForm):
    """Колдонуучунун профилин өзгөртүү формасы"""
    
    class Meta:
        model = UserProfile
        fields = [
            'profile_photo', 'phone_number', 'birth_date', 'gender', 
            'address', 'bio', 'emergency_contact_name', 'emergency_contact_phone'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Өзүңүз жөнүндө кыскача маалымат бериңиз...'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+996 XXX XXX XXX'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+996 XXX XXX XXX'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        labels = {
            'profile_photo': 'Профил сүрөтү',
            'phone_number': 'Телефон номери',
            'birth_date': 'Туулган күнү',
            'gender': 'Жынысы',
            'address': 'Дареги',
            'bio': 'Өзү жөнүндө',
            'emergency_contact_name': 'Тез кырдаал учурундагы байланышуучу',
            'emergency_contact_phone': 'Тез кырдаал телефону',
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Кыргызстандын телефон номеринин форматын текшерүү
            phone_pattern = r'^\+996\d{9}$|^0\d{9}$|\d{9}$'
            if not re.match(phone_pattern, phone.replace(' ', '').replace('-', '')):
                raise ValidationError('Туура телефон номерин киргизиңиз (мисалы: +996700123456)')
        return phone

    def clean_emergency_contact_phone(self):
        phone = self.cleaned_data.get('emergency_contact_phone')
        if phone:
            phone_pattern = r'^\+996\d{9}$|^0\d{9}$|\d{9}$'
            if not re.match(phone_pattern, phone.replace(' ', '').replace('-', '')):
                raise ValidationError('Туура телефон номерин киргизиңиз (мисалы: +996700123456)')
        return phone

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo:
            # Файлдын өлчөмүн текшерүү (5MB)
            if photo.size > 5 * 1024 * 1024:
                raise ValidationError('Сүрөттүн өлчөмү 5MB дан көп болбошу керек.')
            
            # Файлдын типин текшерүү
            if not photo.content_type.startswith('image/'):
                raise ValidationError('Сүрөт файлын гана жүктөө мүмкүн.')
        
        return photo


class UserUpdateForm(forms.ModelForm):
    """User моделинин негизги маалыматтарын өзгөртүү"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'first_name': 'Аты',
            'last_name': 'Фамилиясы',
            'email': 'Email',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Башка колдонуучулардын арасынан ушул email менен дагы бирөө бар беле текшерүү
            if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Бул email дарек буга чейин колдонулгон.')
        return email


class PasswordChangeCustomForm(forms.Form):
    """Сыр сөздү өзгөртүү формасы"""
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Азыркы сыр сөз'
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Жаңы сыр сөз'
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Жаңы сыр сөздү кайталаңыз'
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError('Азыркы сыр сөз туура эмес.')
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')

        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError('Жаңы сыр сөздөр дал келген жок.')

        return cleaned_data

class ScheduleEditForm(forms.Form):
    subject = forms.ModelChoiceField(queryset=Subject.objects.all(), empty_label="Тандаңыз")
    group = forms.ModelChoiceField(queryset=Group.objects.all(), empty_label="Тандаңыз")
    day = forms.ChoiceField(choices=Schedule.DAY_CHOICES, required=True)
    start_time = forms.TimeField(required=True)
    end_time = forms.TimeField(required=True)

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'leave_type': 'Бошотуунун түрү',
            'start_date': 'Башталуу күнү',
            'end_date': 'Аяктоо күнү', 
            'reason': 'Себеби',
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError('Башталуу күнү аяктоо күнүнөн кийинки болушу мүмкүн эмес.')
        
        return cleaned_data
    
class StudentRegistrationForm(UserCreationForm):
    name = forms.CharField(max_length=100, label='Студенттин аты-жөнү')
    course = forms.ModelChoiceField(queryset=Course.objects.all(), label='Курс')
    group = forms.ModelChoiceField(queryset=Group.objects.all(), label='Топ')
    parent_username = forms.CharField(max_length=150, required=False, label='Ата-эненин колдонуучу аты')

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'name', 'course', 'group', 'parent_username']

    def clean_parent_username(self):
        parent_username = self.cleaned_data.get('parent_username')
        if parent_username:
            try:
                parent = User.objects.get(username=parent_username)
                if not parent.userprofile or parent.userprofile.role != 'PARENT':
                    raise forms.ValidationError('Бул колдонуучу ата-эне ролунда эмес.')
            except User.DoesNotExist:
                raise forms.ValidationError('Мындай колдонуучу жок.')
            return parent_username
        return None

class NotificationForm(forms.ModelForm):
    student = forms.ModelChoiceField(queryset=Student.objects.all(), label='Студент')
    message = forms.CharField(widget=forms.Textarea, label='Билдирүү')

    class Meta:
        model = Notification
        fields = ['student', 'message']