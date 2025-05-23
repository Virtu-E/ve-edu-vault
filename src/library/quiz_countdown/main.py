import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Union

from django.urls import reverse
from qstash import QStash, Receiver
from qstash.message import PublishResponse, PublishUrlGroupResponse

from src.config.django import base

logger = logging.getLogger(__name__)

QSTASH_TOKEN = getattr(base, "QSTASH_TOKEN", "")
QSTASH_CURRENT_SIGNING_KEY = getattr(base, "QSTASH_CURRENT_SIGNING_KEY", "")
QSTASH_NEXT_SIGNING_KEY = getattr(base, "QSTASH_NEXT_SIGNING_KEY", "")
SITE_URL = getattr(base, "SITE_URL", "")

qstash = QStash(token=QSTASH_TOKEN)
receiver = Receiver(
    current_signing_key=QSTASH_CURRENT_SIGNING_KEY,
    next_signing_key=QSTASH_NEXT_SIGNING_KEY,
)


@dataclass
class AssessmentTimerData:
    """Data container for assessment timer information.

    Attributes:
        assessment_id: Unique identifier for the assessment
        student_id: ID of the student taking the assessment
        started_at: Timestamp when the assessment was started
        assessment_duration_seconds: Duration of the assessment in seconds
    """

    assessment_id: str
    student_id: int
    started_at: datetime
    assessment_duration_seconds: int


def get_webhook_url(assessment_id: str) -> str:
    """Construct the full webhook URL for an assessment expiration endpoint.

    Args:
        assessment_id: Unique identifier for the assessment

    Returns:
        str: Complete URL for the assessment expiration webhook
    """
    relative_url = reverse(
        "assessments:assessment-expire", kwargs={"assessment_id": assessment_id}
    )
    full_url = f"{SITE_URL}{relative_url}"
    # full_url = "https://webhook.site/155a7d00-9e55-4b22-bff3-1dffcdbdb4c9"
    return full_url


def schedule_test_assessment(
    data: AssessmentTimerData,
) -> Union[PublishResponse, List[PublishUrlGroupResponse]]:
    """Schedule an assessment expiration webhook using QStash.

    Args:
        data: AssessmentTimerData containing all necessary information
             for scheduling the assessment expiration

    Returns:
        str: QStash message ID for the scheduled task
    """
    assessment_data = {
        "assessment_id": data.assessment_id,
        "student_id": data.student_id,
        "started_at": data.started_at.isoformat(),
    }

    end_time = datetime.now() + timedelta(seconds=data.assessment_duration_seconds)
    webhook_url = get_webhook_url(data.assessment_id)

    logger.info(
        "Scheduling assessment expiration webhook - ID: %s, Student: %s, Duration: %s seconds, End time: %s",
        data.assessment_id,
        data.student_id,
        data.assessment_duration_seconds,
        end_time.isoformat(),
    )

    response = qstash.message.publish(
        url=webhook_url,
        body=json.dumps(assessment_data),
        delay=data.assessment_duration_seconds,
        retries=3,
    )

    logger.info(
        "Assessment expiration scheduled - ID: %s, QStash message ID: %s",
        data.assessment_id,
        response,
    )

    return response
