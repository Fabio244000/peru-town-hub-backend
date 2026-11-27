from .base import *  # noqa

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
MAILERS = {'default': {'BACKEND': 'django.core.mail.backends.locmem.EmailBackend'}}
