#!/usr/bin/env python3

import os
import sys
import django

# Django орнотуу
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_system.settings')
sys.path.append('/Users/k_beknazarovicloud.com/Desktop/su_attendance')
django.setup()

from django.contrib.auth.models import User

try:
    admin = User.objects.get(username='admin')
    print(f'Admin username: {admin.username}')
    print(f'Admin email: {admin.email}')
    print(f'Admin is active: {admin.is_active}')
    print(f'Admin is superuser: {admin.is_superuser}')
    print(f'Admin last login: {admin.last_login}')
    print(f'Password check for "admin123": {admin.check_password("admin123")}')
    print(f'Password check for "admin": {admin.check_password("admin")}')
    
    # UserProfile барбы текшереймин
    from core.models import UserProfile
    try:
        profile = UserProfile.objects.get(user=admin)
        print(f'Admin profile role: {profile.role}')
    except UserProfile.DoesNotExist:
        print('Admin UserProfile жок!')
        
except User.DoesNotExist:
    print('Admin колдонуучусу табылган жок!')
except Exception as e:
    print(f'Ката: {e}')