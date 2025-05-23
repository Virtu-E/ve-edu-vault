import logging
from functools import wraps

from django.http import JsonResponse

from src.library.scheduler.config import RECEIVER, get_webhook_url

logger = logging.getLogger(__name__)


def qstash_verification_required(view_func):
    """
    Decorator to verify requests come from QStash.
    Denies all non-QStash requests.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:

            signature = request.headers.get("Upstash-Signature")
            if not signature:
                logger.warning("Missing Upstash-Signature header")
                return JsonResponse({"error": "Unauthorized"}, status=401)

            body = request.body.decode("utf-8")

            RECEIVER.verify(
                body=body,
                signature=signature,
                url=get_webhook_url(),
            )

            logger.info("QStash signature verified successfully")
            return view_func(request, *args, **kwargs)

        except Exception as e:
            logger.exception(f"QStash verification failed: {str(e)}")
            return JsonResponse({"error": "Unauthorized"}, status=401)

    return wrapper
