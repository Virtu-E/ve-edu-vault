# ruff: noqa
import os

os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017/test_db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("SITE_URL", "http://testserver")
os.environ.setdefault(
    "CELERY_BROKER_URL", "redis://localhost:6379/0"
)  # Use Redis or remove entirely
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-32-characters-long")
os.environ.setdefault("LTI_LAUNCH_URL", "http://testserver/lti/launch")
os.environ.setdefault("FRONT_END_URL", "http://testserver")
os.environ.setdefault("QSTASH_URL", "http://test-qstash")
os.environ.setdefault("QSTASH_TOKEN", "test-token")
os.environ.setdefault("QSTASH_CURRENT_SIGNING_KEY", "test-key")
os.environ.setdefault("QSTASH_NEXT_SIGNING_KEY", "test-key")

# NoSQL database environment variables
os.environ.setdefault("NO_SQL_DATABASE_NAME", "test_database")
os.environ.setdefault("NO_SQL_QUESTIONS_DATABASE_NAME", "test_questions_database")
os.environ.setdefault("NO_SQL_ATTEMPTS_DATABASE", "test_attempts_database")
os.environ.setdefault(
    "NO_SQL_GRADING_RESPONSE_DATABASE_NAME", "test_grading_response_database"
)
from src.config.django.base import *  # noqa: F401

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent  # noqa: F401

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()


# Disable Celery tasks for testing
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

LOGGING_CONFIG = None

MEDIA_ROOT = "/tmp/test_media"
STATIC_ROOT = "/tmp/test_static"

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
