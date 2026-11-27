from .base import *  # noqa
from .base import BASE_DIR, LOGGING, MIDDLEWARE

DEBUG = False

# whitenoise goes right after SecurityMiddleware (its docs).
_SECURITY_MIDDLEWARE = MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')
MIDDLEWARE = [
    *MIDDLEWARE[: _SECURITY_MIDDLEWARE + 1],
    'whitenoise.middleware.WhiteNoiseMiddleware',
    *MIDDLEWARE[_SECURITY_MIDDLEWARE + 1 :],
]

# One JSON line per event: CloudWatch keeps a traceback in one event.
LOGGING['handlers']['console']['formatter'] = 'json'

STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    },
}

# Stage is served over plain HTTP (no domain or TLS), so HTTPS-only
# deployment checks don't apply: HSTS, SSL redirect, secure cookies.
SILENCED_SYSTEM_CHECKS = [
    'security.W004',
    'security.W008',
    'security.W012',
    'security.W016',
]
