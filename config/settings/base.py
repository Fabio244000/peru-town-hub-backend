from datetime import timedelta
from pathlib import Path
from typing import Any

import environ

from apps.core.constants import JWT_AUDIENCE, JWT_ISSUER, JWT_LEEWAY_SECONDS

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env.bool('DJANGO_DEBUG', default=False)
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=[])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'rest_framework_simplejwt.token_blacklist',
    'apps.core',
    'apps.common',
    'apps.health',
    'apps.accounts',
    'apps.locations',
]

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    # First: every log line of the request, even another middleware's, carries its id.
    'apps.core.middleware.RequestIdMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('POSTGRES_DB'),
        'USER': env('POSTGRES_USER'),
        'PASSWORD': env('POSTGRES_PASSWORD'),
        'HOST': env('POSTGRES_HOST'),
        'PORT': env('POSTGRES_PORT'),
        'CONN_MAX_AGE': 60,
        'CONN_HEALTH_CHECKS': True,
    }
}

# R3 and R4 of ticket xa367ije83 replace Django's validators.
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'apps.accounts.validators.PasswordConditionsValidator'},
    {'NAME': 'apps.accounts.validators.PasswordSimilarityValidator'},
]

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache',
    }
}

# API routes hang from <API_PREFIX>/<API_URL_VERSION>/ (e.g. api/v1/)
API_PREFIX = 'api'
API_URL_VERSION = 'v1'

# DRF settings
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'apps.core.exception_handlers.custom_exception_handler',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    # Deny by default: a public API says so (conventions/security.md §2).
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    # The base limit of every API; an API with its own limit replaces it.
    'DEFAULT_THROTTLE_CLASSES': [
        'apps.core.throttles.BaseAnonRateThrottle',
        'apps.core.throttles.BaseUserRateThrottle',
    ],
    # No proxy in front of the EC2: the client's IP is REMOTE_ADDR, never a header.
    'NUM_PROXIES': 0,
    'DEFAULT_RENDERER_CLASSES': [
        'apps.core.renderers.EnvelopeJSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# SWAGGER settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Community Town API',
    'VERSION': env('API_VERSION', default='1.0.0'),
    'SERVE_INCLUDE_SCHEMA': False,
}

LOGGING: dict[str, Any] = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'request_id': {'()': 'apps.core.logging.RequestIdFilter'},
    },
    'formatters': {
        'text': {
            'format': '{asctime} {levelname} {name} [{request_id}] {message}',
            'style': '{',
        },
        'json': {'()': 'apps.core.logging.JsonFormatter'},
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'filters': ['request_id'],
            'formatter': 'text',
        },
    },
    'root': {'handlers': ['console'], 'level': env('DJANGO_LOG_LEVEL', default='INFO')},
}


# Accounts (ticket xa367ije83, §9.8)
SUPPORT_EMAIL = env('SUPPORT_EMAIL')
JWT_SIGNING_KEY = env('JWT_SIGNING_KEY')
JWT_ACCESS_TOKEN_MINUTES = env.int('JWT_ACCESS_TOKEN_MINUTES', default=15)
JWT_REFRESH_TOKEN_DAYS = env.int('JWT_REFRESH_TOKEN_DAYS', default=7)
SIGNUP_RATE_PER_HOUR = env.int('SIGNUP_RATE_PER_HOUR', default=10)
SIGNUP_RATE_PER_MONTH = env.int('SIGNUP_RATE_PER_MONTH', default=100)
USERNAME_CHECK_RATE_PER_MINUTE = env.int('USERNAME_CHECK_RATE_PER_MINUTE', default=60)
API_ANON_RATE_PER_MINUTE = env.int('API_ANON_RATE_PER_MINUTE', default=120)
API_USER_RATE_PER_MINUTE = env.int('API_USER_RATE_PER_MINUTE', default=240)

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=JWT_ACCESS_TOKEN_MINUTES),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=JWT_REFRESH_TOKEN_DAYS),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': JWT_SIGNING_KEY,
    'ISSUER': JWT_ISSUER,
    'AUDIENCE': JWT_AUDIENCE,
    'LEEWAY': JWT_LEEWAY_SECONDS,
    'USER_ID_FIELD': 'uuid',
}
