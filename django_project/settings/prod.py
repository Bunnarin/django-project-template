from .base import *
from decouple import config

DEBUG = False
ALLOWED_HOSTS = [config('DOMAIN')]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True 
EMAIL_HOST_USER = config('SUPERUSER_EMAIL')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# Required for when you are behind a reverse proxy like Nginx that handles SSL.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
# use the X-Forwarded-Host header to get the domain name when constructing absolute URLs
USE_X_FORWARDED_HOST = True

