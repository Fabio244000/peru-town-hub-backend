from .base import *  # noqa
from .base import env

DEBUG = True

LOGGING = {
    'version': 1,
    'disable_existing_logger': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'verbose',
        },
    },
    'root': {'handler': ['console'], 'level': env('DJANGO_LOG_LEVEL', default='INFO')},
}
