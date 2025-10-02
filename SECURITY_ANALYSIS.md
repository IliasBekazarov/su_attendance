# 🚨 КООПСУЗДУК КӨЙГӨЙЛӨРҮ ЖАНА ЧЕЧҮҮЛӨРҮ

## 1. SECRET_KEY коркунучу
**Көйгөй:** settings.py файлында SECRET_KEY ачык жазылган
**Чечүү:**

```python
# settings.py
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-key-only-for-dev')

# .env файлы түзүү керек
# SECRET_KEY=your-super-secure-random-key-here
# DEBUG=False
# DATABASE_URL=postgresql://user:pass@localhost/db
```

## 2. CSRF Protection өчүрүлгөн
**Көйгөй:** CSRF middleware комментке алынган
**Чечүү:**

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # Кайра кошуу КЕРЕК!
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

## 3. Production Settings жок
**Көйгөй:** Production үчүн жеке settings жок
**Чечүү:**

```python
# settings/base.py
# settings/development.py  
# settings/production.py

# production.py мисалы:
from .base import *
import os

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## 4. API Authentication жок
**Көйгөй:** REST API токен authentication жок
**Чечүү:**

```python
# settings.py
INSTALLED_APPS += [
    'rest_framework.authtoken',
    'corsheaders',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
}
```