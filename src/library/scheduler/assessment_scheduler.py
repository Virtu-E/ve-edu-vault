import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, TypeAlias, Union

from qstash.errors import (
    ChatRateLimitExceededError,
    DailyMessageLimitExceededError,
    QStashError,
    RateLimitExceededError,
)
from qstash.message import PublishResponse, PublishUrlGroupResponse

from ...apps.integrations.webhooks.data_types import WebhookRequest
from ...apps.integrations.webhooks.registry import HandlerTypeEnum
from ...exceptions import SchedulingError
from .config import QSTASH, get_webhook_url

logger = logging.getLogger(__name__)

SchedulerResponse: TypeAlias = Union[PublishResponse, List[PublishUrlGroupResponse]]


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


def schedule_test_assessment(
    data: AssessmentTimerData,
) -> SchedulerResponse:
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

    scheduled_data = WebhookRequest(
        event_type=HandlerTypeEnum.ASSESSMENT_EXPIRATION.value,
        event_id=f"{data.assessment_id}-{data.student_id}",
        timestamp=data.started_at,
        data=assessment_data,
    )

    end_time = datetime.now() + timedelta(seconds=data.assessment_duration_seconds)

    logger.info(
        "Scheduling assessment expiration webhook - ID: %s, Student: %s, Duration: %s seconds, End time: %s",
        data.assessment_id,
        data.student_id,
        data.assessment_duration_seconds,
        end_time.isoformat(),
    )
    try:
        response = QSTASH.message.publish(
            url=get_webhook_url(),
            body=json.dumps(scheduled_data.model_dump(mode="json")),
            delay=data.assessment_duration_seconds,
            retries=3,
        )
        logger.info(
            "Assessment expiration scheduled - ID: %s, QStash message ID: %s",
            data.assessment_id,
            response,
        )
        return response
    except (
        QStashError,
        RateLimitExceededError,
        ChatRateLimitExceededError,
        DailyMessageLimitExceededError,
    ) as e:
        raise SchedulingError(
            message=f"Failed to schedule assessment expiration: {str(e)}",
            assessment_id=data.assessment_id,
            student_id=data.student_id,
            duration_seconds=data.assessment_duration_seconds,
            qstash_error=str(e),
            webhook_url=get_webhook_url(),
        ) from e
