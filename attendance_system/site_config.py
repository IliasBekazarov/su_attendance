# -*- coding: utf-8 -*-
"""
Salymbekov University - Attendance System
Site Configuration Settings
"""

# Site Information
SITE_NAME = "Salymbekov University"
SITE_NAME_KY = "Салымбеков Университети" 
SITE_NAME_RU = "Университет Салымбекова"
SITE_NAME_EN = "Salymbekov University"

SITE_DESCRIPTION = "Student Attendance Management System"
SITE_DESCRIPTION_KY = "Студенттердин катышуу системасы"
SITE_DESCRIPTION_RU = "Система учета посещаемости студентов"
SITE_DESCRIPTION_EN = "Student Attendance Management System"

# University Information
UNIVERSITY_INFO = {
    'name': 'Salymbekov University',
    'name_ky': 'Салымбеков Университети',
    'name_ru': 'Университет Салымбекова',
    'name_en': 'Salymbekov University',
    'address': 'Bishkek, Kyrgyzstan',
    'address_ky': 'Бишкек, Кыргызстан',
    'address_ru': 'Бишкек, Кыргызстан', 
    'address_en': 'Bishkek, Kyrgyzstan',
    'phone': '+996 (312) 123-456',
    'email': 'info@salymbekov.kg',
    'website': 'https://salymbekov.kg',
    'founded_year': 1993,
    'logo_url': '/static/css/su_logo.png'
}

# System Configuration
SYSTEM_CONFIG = {
    'version': '1.0.0',
    'build_date': '2025-09-21',
    'developer': 'SU IT Department',
    'contact_email': 'support@salymbekov.kg',
    'support_phone': '+996 (312) 123-457',
    'maintenance_mode': False,
    'debug_mode': False,
    'max_login_attempts': 5,
    'session_timeout_minutes': 60,
    'password_reset_timeout_hours': 24
}

# Default Language Settings
LANGUAGE_CONFIG = {
    'default_language': 'ky',  # Кыргызча по умолчанию
    'available_languages': [
        ('ky', 'Кыргызча', '🇰🇬'),
        ('ru', 'Русский', '🇷🇺'), 
        ('en', 'English', '🇺🇸')
    ],
    'language_switcher_enabled': True,
    'auto_detect_language': True
}

# Theme Configuration
THEME_CONFIG = {
    'default_theme': 'light',
    'available_themes': ['light', 'dark'],
    'theme_switcher_enabled': True,
    'auto_theme_based_on_time': False
}

# Academic Year Settings
ACADEMIC_CONFIG = {
    'current_academic_year': '2024-2025',
    'semester_start_date': '2024-09-01',
    'semester_end_date': '2025-06-30',
    'attendance_required_percentage': 75,
    'max_excused_absences': 10,
    'working_days': ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY'],
    'class_duration_minutes': 90,
    'break_duration_minutes': 10
}

# Notification Settings  
NOTIFICATION_CONFIG = {
    'email_notifications_enabled': True,
    'sms_notifications_enabled': False,
    'push_notifications_enabled': True,
    'notification_retention_days': 30,
    'daily_attendance_summary': True,
    'weekly_attendance_report': True
}

# Security Settings
SECURITY_CONFIG = {
    'force_https': False,
    'csrf_protection_enabled': True,
    'xframe_options': 'DENY',
    'content_type_nosniff': True,
    'browser_xss_filter': True,
    'hsts_max_age': 31536000,
    'require_password_change_days': 90
}

# File Upload Settings
UPLOAD_CONFIG = {
    'max_file_size_mb': 10,
    'allowed_file_types': ['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx', 'xls', 'xlsx'],
    'profile_photo_max_size_mb': 5,
    'document_upload_path': 'uploads/documents/',
    'profile_photo_path': 'uploads/profile_photos/'
}

# Social Media & Contact
SOCIAL_MEDIA = {
    'facebook': 'https://facebook.com/salymbekov.university',
    'instagram': 'https://instagram.com/salymbekov_university', 
    'linkedin': 'https://linkedin.com/school/salymbekov-university',
    'youtube': 'https://youtube.com/c/SalymbekovUniversity',
    'telegram': 'https://t.me/salymbekov_university'
}

# Footer Information
FOOTER_CONFIG = {
    'copyright_text': '© 2025 Салымбеков Университети. Бардык укуктар корголгон.',
    'copyright_text_ru': '© 2025 Университет Салымбекова. Все права защищены.',
    'copyright_text_en': '© 2025 Salymbekov University. All rights reserved.',
    'show_social_links': True,
    'show_contact_info': True,
    'additional_links': [
        {'name': 'Privacy Policy', 'name_ky': 'Купуялык саясаты', 'name_ru': 'Политика конфиденциальности', 'url': '/privacy/'},
        {'name': 'Terms of Service', 'name_ky': 'Кызмат көрсөтүү шарттары', 'name_ru': 'Условия использования', 'url': '/terms/'},
        {'name': 'Help & Support', 'name_ky': 'Жардам', 'name_ru': 'Помощь и поддержка', 'url': '/help/'}
    ]
}