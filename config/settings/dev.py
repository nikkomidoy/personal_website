from .base import *  # noqa: F403
from .base import env_list

DEBUG = True
SECRET_KEY = "django-insecure-dev-only-change-me"
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0")
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Plain static storage so tests and runserver don't need collectstatic.
STORAGES["staticfiles"] = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}  # noqa: F405
