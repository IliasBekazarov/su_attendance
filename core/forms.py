from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Student, Course, Group, Notification, Schedule, LeaveRequest
from django import forms
from .models import Subject, Group

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