"""Production settings, configured entirely through environment variables (see .env.example)."""

import os

from .base import *  # noqa: F403
from .base import env_bool, env_list

DEBUG = False
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

# TLS terminates at the Application Load Balancer.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
SESSION_COOKIE_SECURE = SECURE_SSL_REDIRECT
CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "SAMEORIGIN"

# User uploads (images, résumé PDFs) go to S3. Credentials come from the ECS task IAM role.
if os.environ.get("AWS_STORAGE_BUCKET_NAME"):
    AWS_STORAGE_BUCKET_NAME = os.environ["AWS_STORAGE_BUCKET_NAME"]
    AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", os.environ.get("AWS_REGION"))
    AWS_S3_CUSTOM_DOMAIN = os.environ.get("AWS_S3_CUSTOM_DOMAIN")  # e.g. a CloudFront domain
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_LOCATION = "media"
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    STORAGES["default"] = {"BACKEND": "storages.backends.s3.S3Storage"}  # noqa: F405

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
