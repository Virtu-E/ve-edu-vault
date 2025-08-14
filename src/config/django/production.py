from django.utils import timezone

from src.config.django.base import *

DEBUG = False


# =============================================================================
# SECURITY
# =============================================================================

# Host Security
ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".virtueducate.com"]

# HTTPS Settings

# Security Headers
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# X_FRAME_OPTIONS = "DENY"
#
# # Cookie Security
# SESSION_COOKIE_HTTPONLY = True
# CSRF_COOKIE_HTTPONLY = True
# SESSION_COOKIE_SAMESITE = "Lax"
# CSRF_COOKIE_SAMESITE = "Lax"


# Csrf settings

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# CSRF Trusted Origins
# CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", cast=Csv())
# CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", cast=Csv())

CSRF_TRUSTED_ORIGINS = [
    "https://virtueducate.com",
    "https://www.virtueducate.com",
    "https://learn.virtueducate.com",
    "https://vault.virtueducate.com",
    "https://www.vault.virtueducate.com",
    "https://studio.lms.virtueducate.com",
    "https://lms.virtueducate.com",
    "https://www.learn.virtueducate.com",
]

CORS_ALLOWED_ORIGINS = [
    "https://virtueducate.com",
    "https://www.virtueducate.com",
    "https://learn.virtueducate.com",
    "https://vault.virtueducate.com",
    "https://www.vault.virtueducate.com",
    "https://studio.lms.virtueducate.com",
    "https://lms.virtueducate.com",
    "https://www.learn.virtueducate.com",
]

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB"),
        "USER": config("POSTGRES_USER"),
        "PASSWORD": config("POSTGRES_PASSWORD"),
        "HOST": config("POSTGRES_HOST", default="localhost"),
        "PORT": config("POSTGRES_PORT", default=5432, cast=int),
        "CONN_MAX_AGE": 600,  # Connection pooling
    }
}

# =============================================================================
# CONTENT SECURITY POLICY (CSP)
# =============================================================================

# CSP Configuration
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",  # Remove this gradually as you implement nonces
    "https://cdnjs.cloudflare.com",
    "'nonce-{nonce}'",  # Use nonces for inline scripts
)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_CONNECT_SRC = ("'self'", "wss:", "ws:")
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)


# =============================================================================
# STATIC FILES & MEDIA
# =============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = "/app/staticfiles"


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
# FILE UPLOAD SECURITY
# =============================================================================

# File upload security
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Allowed file types for uploads
ALLOWED_UPLOAD_EXTENSIONS = [".pdf", ".doc", ".docx", ".txt", ".jpg", ".jpeg", ".png"]
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


# =============================================================================
# ENVIRONMENT INFO
# =============================================================================


def get_environment_info():
    return f"Prod Server - {timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')}"


ENVIRONMENT_NAME = get_environment_info()
ENVIRONMENT_COLOR = "#dc3545"
