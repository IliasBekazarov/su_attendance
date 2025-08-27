from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from .serializers import NotificationSerializer
from django.core.mail import send_mail
from django.dispatch import receiver
from django.db.models.signals import post_save
from attendance.models import AttendanceRecord
from accounts.permissions import IsParent

@receiver(post_save, sender=AttendanceRecord)
def send_notification(sender, instance, created, **kwargs):
    if created and instance.status in ('absent', 'late'):
        parent = instance.student.student_profile.parent
        if parent:
            subject = f'Attendance Alert for {instance.student.username}'
            message = f'Your child was {instance.status} on {instance.date}.'
            send_mail(subject, message, 'from@example.com', [parent.email])
            Notification.objects.create(user=parent, message=message)

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)