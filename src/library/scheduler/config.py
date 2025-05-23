import logging
from urllib.parse import urljoin

from django.urls import reverse
from qstash import QStash, Receiver

from src.config.django import base

QSTASH_TOKEN = getattr(base, "QSTASH_TOKEN", "")
QSTASH_CURRENT_SIGNING_KEY = getattr(base, "QSTASH_CURRENT_SIGNING_KEY", "")
QSTASH_NEXT_SIGNING_KEY = getattr(base, "QSTASH_NEXT_SIGNING_KEY", "")
SITE_URL = getattr(base, "SITE_URL", "")

QSTASH = QStash(token=QSTASH_TOKEN)
RECEIVER = Receiver(
    current_signing_key=QSTASH_CURRENT_SIGNING_KEY,
    next_signing_key=QSTASH_NEXT_SIGNING_KEY,
)

logger = logging.getLogger(__name__)


def get_webhook_url() -> str:
    """Construct the full webhook URL for an assessment expiration endpoint.

    Returns:
        str: Complete URL for the assessment expiration webhook
    """
    relative_url = reverse("webhook:assessments-webhook")

    # urljoin handles the slashes correctly
    full_url = urljoin(SITE_URL, relative_url)

    logger.debug(f"Constructed webhook URL: {full_url}")
    return full_url
