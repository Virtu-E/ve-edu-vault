import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, TypeAlias, Union

from qstash.errors import (ChatRateLimitExceededError,
                           DailyMessageLimitExceededError, QStashError,
                           RateLimitExceededError)
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
        block_id : ID of the targetd Learning Objective
    """

    assessment_id: str
    student_id: int
    started_at: datetime
    assessment_duration_seconds: int
    block_id: str


def schedule_test_assessment(
    data: AssessmentTimerData,
) -> SchedulerResponse:
    """Schedule an assessment expiration webhook using QStash."""

    assessment_data = {
        "assessment_id": data.assessment_id,
        "student_id": data.student_id,
        "started_at": data.started_at.isoformat(),
        "block_id": data.block_id,
    }

    scheduled_data = WebhookRequest(
        event_type=HandlerTypeEnum.ASSESSMENT_EXPIRATION.value,
        event_id=f"{data.assessment_id}-{data.student_id}",
        timestamp=data.started_at,
        data=assessment_data,
    )

    # Wrap the webhook data in event_metadata to match what the handler expects
    payload = {"event_metadata": scheduled_data.model_dump(mode="json")}

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
            body=json.dumps(payload),
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
