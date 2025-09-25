# 🏗️ АРХИТЕКТУРА ЖАКШЫРТУУ ПЛАНЫ

## ЭТАП 1: КООПСУЗДУК ЖАКШЫРТУУ (1-2 жума)

### 1.1 Environment Configuration
```bash
pip install python-dotenv django-cors-headers
```

```python
# .env
SECRET_KEY=your-super-secure-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 1.2 Settings жөнгө салуу
```python
# attendance_system/settings/__init__.py
import os
from .base import *

if os.getenv('DJANGO_ENV') == 'production':
    from .production import *
else:
    from .development import *
```

### 1.3 API Authentication
```python
# core/authentication.py
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _

class ExpiringTokenAuthentication(TokenAuthentication):
    """Убакыт мөөнөтү бар токенди authentication"""
    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise AuthenticationFailed(_('Invalid token.'))

        if not token.user.is_active:
            raise AuthenticationFailed(_('User inactive or deleted.'))

        # Токендин мөөнөтүн текшерүү (24 сааттан ашык болбосун)
        from django.utils import timezone
        from datetime import timedelta
        if token.created < timezone.now() - timedelta(hours=24):
            raise AuthenticationFailed(_('Token has expired.'))

        return (token.user, token)
```

## ЭТАП 2: QR-КОД СИСТЕМА (2-3 жума)

### 2.1 QR Code Models
```python
# core/models.py ичине кошуу
import uuid
from django.utils import timezone

class QRAttendanceSession(models.Model):
    """QR код аркылуу катышуу сессиясы"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schedule = models.ForeignKey('Schedule', on_delete=models.CASCADE)
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE)
    qr_code = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    location_latitude = models.FloatField(null=True, blank=True)
    location_longitude = models.FloatField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.qr_code:
            self.qr_code = str(uuid.uuid4())
        if not self.expires_at:
            # 10 мүнөт мөөнөт
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"QR Session - {self.schedule.subject.name} - {self.created_at}"

class QRAttendance(models.Model):
    """QR аркылуу белгиленген катышуу"""
    qr_session = models.ForeignKey(QRAttendanceSession, on_delete=models.CASCADE)
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    attendance = models.OneToOneField('Attendance', on_delete=models.CASCADE)
    scanned_at = models.DateTimeField(auto_now_add=True)
    device_info = models.JSONField(default=dict, blank=True)
    
    class Meta:
        unique_together = ['qr_session', 'student']
```

### 2.2 QR Code API Views
```python
# core/api_views.py ичине кошуу
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import qrcode
from io import BytesIO
import base64
from django.http import JsonResponse

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_qr_session(request):
    """Мугалим үчүн QR сессия түзүү"""
    if request.user.userprofile.role != 'TEACHER':
        return Response({'error': 'Only teachers can generate QR codes'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    schedule_id = request.data.get('schedule_id')
    try:
        schedule = Schedule.objects.get(id=schedule_id, subject__teacher__user=request.user)
        teacher = Teacher.objects.get(user=request.user)
        
        # Активдүү сессияны текшерүү
        existing_session = QRAttendanceSession.objects.filter(
            schedule=schedule,
            is_active=True,
            expires_at__gt=timezone.now()
        ).first()
        
        if existing_session:
            qr_data = existing_session.qr_code
        else:
            # Жаңы сессия түзүү
            session = QRAttendanceSession.objects.create(
                schedule=schedule,
                teacher=teacher
            )
            qr_data = session.qr_code
        
        # QR код генерация кылуу
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return Response({
            'qr_code': qr_data,
            'qr_image': f"data:image/png;base64,{img_str}",
            'expires_at': existing_session.expires_at if existing_session else session.expires_at
        })
        
    except Schedule.DoesNotExist:
        return Response({'error': 'Schedule not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_qr_attendance(request):
    """Студент QR кодду scan кылып катышуу белгилөө"""
    if request.user.userprofile.role != 'STUDENT':
        return Response({'error': 'Only students can scan QR codes'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    qr_code = request.data.get('qr_code')
    device_info = request.data.get('device_info', {})
    
    try:
        student = Student.objects.get(user=request.user)
        qr_session = QRAttendanceSession.objects.get(
            qr_code=qr_code,
            is_active=True
        )
        
        # Мөөнөтүн текшерүү
        if qr_session.is_expired:
            return Response({'error': 'QR code has expired'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Студент бул сабакта болушу керекпи текшерүү
        if qr_session.schedule.group != student.group:
            return Response({'error': 'You are not enrolled in this class'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Мурда белгиленген катышуу барбы текшерүү
        existing_qr_attendance = QRAttendance.objects.filter(
            qr_session=qr_session,
            student=student
        ).first()
        
        if existing_qr_attendance:
            return Response({'error': 'Attendance already marked'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Attendance түзүү же жаңылоо
        attendance, created = Attendance.objects.get_or_create(
            student=student,
            subject=qr_session.schedule.subject,
            date=date.today(),
            defaults={'status': 'Present'}
        )
        
        if not created:
            attendance.status = 'Present'
            attendance.save()
        
        # QR attendance record түзүү
        QRAttendance.objects.create(
            qr_session=qr_session,
            student=student,
            attendance=attendance,
            device_info=device_info
        )
        
        return Response({
            'message': 'Attendance marked successfully',
            'subject': qr_session.schedule.subject.name,
            'status': 'Present'
        })
        
    except QRAttendanceSession.DoesNotExist:
        return Response({'error': 'Invalid QR code'}, 
                       status=status.HTTP_404_NOT_FOUND)
    except Student.DoesNotExist:
        return Response({'error': 'Student profile not found'}, 
                       status=status.HTTP_404_NOT_FOUND)
```

## ЭТАП 3: TWO-FACTOR AUTHENTICATION (2-3 жума)

### 3.1 2FA Models
```python
# core/models.py ичине кошуу
import pyotp
import qrcode
from io import BytesIO
import base64

class TwoFactorAuth(models.Model):
    """Эки факторлуу аутентификация"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    secret_key = models.CharField(max_length=32)
    is_enabled = models.BooleanField(default=False)
    backup_codes = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.secret_key:
            self.secret_key = pyotp.random_base32()
        super().save(*args, **kwargs)
    
    def get_qr_code(self):
        """Google Authenticator үчүн QR код"""
        totp_uri = pyotp.totp.TOTP(self.secret_key).provisioning_uri(
            name=self.user.email,
            issuer_name="SU Attendance System"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_token(self, token):
        """TOTP токенди текшерүү"""
        totp = pyotp.TOTP(self.secret_key)
        return totp.verify(token, valid_window=1)
    
    def generate_backup_codes(self):
        """Резервдик коддорду генерация кылуу"""
        import secrets
        import string
        
        codes = []
        for _ in range(10):
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) 
                          for _ in range(8))
            codes.append(code)
        
        self.backup_codes = codes
        self.save()
        return codes
```

### 3.2 2FA API Views
```python
# core/api_views.py ичине кошуу

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enable_2fa(request):
    """2FA иштетүү"""
    two_factor, created = TwoFactorAuth.objects.get_or_create(user=request.user)
    
    if not created and two_factor.is_enabled:
        return Response({'error': '2FA is already enabled'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    qr_code = two_factor.get_qr_code()
    backup_codes = two_factor.generate_backup_codes()
    
    return Response({
        'qr_code': qr_code,
        'secret_key': two_factor.secret_key,
        'backup_codes': backup_codes
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_2fa_setup(request):
    """2FA жөндөөнү текшерүү"""
    token = request.data.get('token')
    
    try:
        two_factor = TwoFactorAuth.objects.get(user=request.user)
        
        if two_factor.verify_token(token):
            two_factor.is_enabled = True
            two_factor.save()
            return Response({'message': '2FA enabled successfully'})
        else:
            return Response({'error': 'Invalid token'}, 
                          status=status.HTTP_400_BAD_REQUEST)
            
    except TwoFactorAuth.DoesNotExist:
        return Response({'error': '2FA not set up'}, 
                       status=status.HTTP_404_NOT_FOUND)

# Custom authentication backend 2FA үчүн
# core/backends.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

class TwoFactorBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, token=None):
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                # 2FA текшерүү
                if hasattr(user, 'twofactorauth') and user.twofactorauth.is_enabled:
                    if token and user.twofactorauth.verify_token(token):
                        return user
                    return None
                else:
                    return user
        except User.DoesNotExist:
            return None
        return None
```

## ЭТАП 4: ADVANCED STATISTICS & REAL-TIME (3-4 жума)

### 4.1 Statistics Models
```python
# core/models.py ичине кошуу
class AttendanceStatistics(models.Model):
    """Катышуу статистикасы кэшталган маалыматтар"""
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    date_from = models.DateField()
    date_to = models.DateField()
    
    total_classes = models.IntegerField(default=0)
    present_count = models.IntegerField(default=0)
    absent_count = models.IntegerField(default=0)
    late_count = models.IntegerField(default=0)
    excused_count = models.IntegerField(default=0)
    
    attendance_percentage = models.FloatField(default=0.0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'subject', 'date_from', 'date_to']
```

### 4.2 Real-time Updates (WebSocket)
```python
# pip install channels channels-redis

# attendance_system/settings.py
INSTALLED_APPS += [
    'channels',
]

ASGI_APPLICATION = 'attendance_system.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# core/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class AttendanceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = f"attendance_{self.scope['user'].id}"
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_attendance_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'attendance_update',
            'data': event['data']
        }))
```

## ЭТАП 5: CLOUD DEPLOYMENT (4-6 жума)

### 5.1 Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "attendance_system.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### 5.2 AWS/Azure Deployment
```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/attendance
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    environment:
      POSTGRES_DB: attendance
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:alpine

volumes:
  postgres_data:
```

## УБАКЫТ ПЛАНЫ:
- **1-2 жума**: Коопсуздук жакшыртуу
- **2-3 жума**: QR-код система  
- **2-3 жума**: 2FA система
- **3-4 жума**: Advanced статистика
- **4-6 жума**: Cloud deployment

**Жалпы**: 12-18 жума (3-4 ай)