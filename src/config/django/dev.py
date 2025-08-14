from decouple import Csv
from django.utils import timezone

from src.config.django.base import *  # noqa: F401

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB"),
        "USER": config("POSTGRES_USER"),
        "PASSWORD": config("POSTGRES_PASSWORD"),
        "HOST": config("POSTGRES_HOST"),
        "PORT": config("POSTGRES_PORT"),
    }
}

CORS_ALLOW_ALL_ORIGINS = config("CORS_ALLOW_ALL_ORIGINS", default=False, cast=bool)
CORS_ALLOW_CREDENTIALS = config("CORS_ALLOW_CREDENTIALS", default=False, cast=bool)

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", cast=Csv())

# =============================================================================
# STATIC FILES & MEDIA
# =============================================================================

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"


# =============================================================================
# RATE LIMITING CONFIGURATION
# =============================================================================

# Rate limiting settings
RATELIMIT_USE_CACHE = "default"
RATELIMIT_ENABLE = True

# Rate limiting thresholds
RATE_LIMIT_AUTH_ATTEMPTS = "5/m"  # 5 login attempts per minute
RATE_LIMIT_API_REQUESTS = "1000/h"  # 1000 API requests per hour
RATE_LIMIT_PASSWORD_RESET = "3/h"  # 3 password reset attempts per hour

# =============================================================================
# ENVIRONMENT INFO
# =============================================================================


def get_environment_info():
    return f"Dev Server - {timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')}"


ENVIRONMENT_NAME = get_environment_info()
ENVIRONMENT_COLOR = "#28a745"
