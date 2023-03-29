"""
Django settings for predishun project.

Generated by 'django-admin startproject' using Django 4.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import os
import logging.config
from django.utils.log import DEFAULT_LOGGING
from pathlib import Path
import environ
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

root = environ.Path(__file__) - 2
dotenv = root(os.environ.get('dotenv', '.env'))
if os.path.exists(dotenv):
    environ.Env.read_env(dotenv)

# Create a directory for storing the log if necessary
os.makedirs(os.path.join(root, 'log'), mode=0o755, exist_ok=True)

SECRET_KEY = os.environ.get("SECRET_KEY") or 'cdhj6q8r&68+0n@l*t9&s$r-!&1%n=uq4x2i(v72ua=23df4dd567d/d89t24,nl0m.s33si&++='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = int(os.environ.get("DEBUG", 1))

# 'ALLOWED_HOSTS' should be a single string of hosts with a space between each.
# For example: 'ALLOWED_HOSTS=localhost 127.0.0.1 [::1]'
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS").split(',') if os.environ.get("ALLOWED_HOSTS") else ['127.0.0.1', '0.0.0.0', 'localhost']

# Application definition

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'dj_rest_auth.registration',
    'allauth.socialaccount',
    'corsheaders',
    'django_redis',
    'debug_toolbar',
    'channels',
    'core',
]

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [f"redis://:{os.environ.get('REDIS_PASSWORD')}@127.0.0.1:6379/1" if os.environ.get('REDIS_PASSWORD') else "redis://127.0.0.1:6379/1"],
        },
    },
}

SITE_ID = 1

# REST_USE_JWT = True

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

INTERNAL_IPS = [
    "127.0.0.1",
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
        # 'rest_framework_simplejwt.authentication.JWTAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}

if not DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
        'rest_framework.renderers.JSONRenderer',
    )

REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'predishun-auth',
    'JWT_AUTH_REFRESH_COOKIE': 'predishun-refresh',
    'PASSWORD_RESET_SERIALIZER': 'core.serializers.CustomPasswordResetSerializer',
}

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda _request: DEBUG
}

AUTHENTICATION_BACKENDS = [
    'allauth.account.auth_backends.AuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=25),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
}

REST_AUTH_REGISTER_SERIALIZERS = {
    'REGISTER_SERIALIZER': 'core.serializers.UserAccountRegisterSerializer',
}

#AUTH_USER_MODEL = 'core.UserAccount'

ROOT_URLCONF = 'predishun.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'core/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:3001',
    'https://predishun.com',
    'http://predishun.com',
]

if os.environ.get('DEBUG') != '1':
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
            },
            'simple': {
                'format': '%(levelname)s %(message)s'
            },
        },
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'log/debug.log',
                'maxBytes' : 1024*1024*10,
                'backupCount' : 10,
                'formatter': 'verbose',
            },
            'console': {  # allow werkzeug debugger in runserver_plus to log console
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django': {  # for all django-internal messages
                'handlers': ['console', 'file'],
                'level': 'ERROR',
                'propagate': True,
            },
            'django.db.backends': {  # for database-related messages
                'handlers': ['file'],
                'level': 'DEBUG',
            },
            'debug': {
                'handlers': ['file'],
                'level': 'DEBUG',
                'propagate': True,
            },
            'werkzeug': {  # allow werkzeug debugger in runserver_plus to log console
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': True,
            }
        },
    }

    CSRF_COOKIE_SECURE = True

    SESSION_COOKIE_SECURE = True

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://:{os.environ.get('REDIS_PASSWORD')}@127.0.0.1:6379/1" if os.environ.get('REDIS_PASSWORD') else "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
        "KEY_PREFIX": "predishun"
    }
}

WSGI_APPLICATION = 'predishun.wsgi.application'

ASGI_APPLICATION = 'predishun.asgi.application'

CACHE_TTL = 15 * 60

ACCOUNT_ADAPTER = 'core.adapter.CustomDefaultAccountAdapter'

ACCOUNT_AUTHENTICATION_METHOD = 'email'

ACCOUNT_EMAIL_REQUIRED = True

ACCOUNT_EMAIL_VERIFICATION = 'mandatory'

ACCOUNT_CONFIRM_EMAIL_ON_GET = True

LOGIN_URL = os.environ.get("CLIENT_LOGIN_URL")

CLIENT_ACTIVATE_ACCOUNT_URL = os.environ.get("CLIENT_ACTIVATE_ACCOUNT_URL")

CLIENT_RESET_PASSWORD_URL = os.environ.get("CLIENT_RESET_PASSWORD_URL")

PAYSTACK_SECRET_KEY = os.environ.get("PAYSTACK_SECRET_KEY")

WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.environ.get("WHATSAPP_WEBHOOK_VERIFY_TOKEN")

WHATSAPP_API_ID = os.environ.get("WHATSAPP_API_ID")

WHATSAPP_API_SECRET = os.environ.get("WHATSAPP_API_SECRET")

WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")

WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN")

WHATSAPP_API_VERSION = os.environ.get("WHATSAPP_API_VERSION")

TELEGRAM_API_ID = os.environ.get("TELEGRAM_API_ID")

TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH")

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

TELEGRAM_PHONE_NUMBER = os.environ.get("TELEGRAM_PHONE_NUMBER")

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_USE_TLS = True

EMAIL_HOST = os.environ.get("EMAIL_HOST")

EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")

EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

EMAIL_PORT = 587

# EMAIL_FILE_PATH = os.path.join(BASE_DIR, 'tmp/email')


# Percentage charge for tipster's pricing
PERCENTAGE_CHARGE = os.environ.get("PERCENTAGE_CHARGE", 0.15)


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        "ENGINE": os.environ.get("RDS_ENGINE", "django.db.backends.postgresql_psycopg2"),
        "NAME": os.environ.get("RDS_DATABASE", "predishun"),
        "USER": os.environ.get("RDS_USER", "postgres"),
        "PASSWORD": os.environ.get("RDS_PASSWORD", "postgres"),
        "HOST": os.environ.get("RDS_HOST", "localhost"),
        "PORT": os.environ.get("RDS_PORT", "5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

# AWS_ACCESS_KEY_ID = '<YOUR AWS ACCESS KEY>'
# AWS_SECRET_ACCESS_KEY = '<YOUR AWS SECRET KEY>'
# AWS_STORAGE_BUCKET_NAME = '<YOUR AWS S3 BUCKET NAME>'
# AWS_S3_SIGNATURE_VERSION = 's3v4'
# AWS_S3_REGION_NAME = '<YOUR AWS S3 BUCKET LOCATION>'
# AWS_S3_FILE_OVERWRITE = False
# AWS_DEFAULT_ACL = None
# AWS_S3_VERIFY = True
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
