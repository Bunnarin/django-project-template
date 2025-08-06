from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DATABASES['default']['HOST'] = 'localhost'

STATIC_ROOT = None
STATICFILES_DIRS = [BASE_DIR / 'static']

