# ruff: noqa
from .common import *  # noqa: F401

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    },
    "OPTIONS": {
        "timeout": 30,  # seconds
    },
}

# Disable Celery tasks for testing
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable Elasticsearch indexing
ELASTICSEARCH_DSL_AUTOSYNC = False
ELASTICSEARCH_DSL_INDEX_SETTINGS = {}


DISABLE_CUSTOM_SIGNAL_PROCESSOR = True
