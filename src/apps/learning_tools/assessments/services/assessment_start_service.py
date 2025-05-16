import logging
from datetime import datetime

from asgiref.sync import sync_to_async

from src.lib.quiz_countdown.main import AssessmentTimerData, schedule_test_assessment
from src.utils.mixins.context import ServiceResources

from ..exceptions import SchedulingError
from ..models import UserAssessmentAttempt

logger = logging.getLogger(__name__)


async def start_assessment(
    *, education_context: ServiceResources
) -> UserAssessmentAttempt:
    """
    Start or retrieve an active assessment for a user based on their learning objective.

    This function first checks if the user already has an active assessment for the given
    learning objective. If one exists, it returns that assessment. Otherwise, it creates
    a new assessment attempt and schedules it with a timer for expiration.

    Args:
        education_context (ServiceResources): Context containing user and learning objective resources.

    Returns:
        UserAssessmentAttempt: The active or newly created assessment attempt.

    Raises:
        SchedulingError: If the assessment timer could not be scheduled.
    """
    user = education_context.resources.user
    learning_objective = education_context.resources.learning_objective

    logger.debug(
        f"Fetching active assessment for user {user.id} and objective {learning_objective.id}"
    )

    if assessment := await sync_to_async(UserAssessmentAttempt.get_active_attempt)(
        user=user, learning_objective=learning_objective
    ):
        logger.info(
            f"Found existing active assessment {assessment.assessment_id} for user {user.id}"
        )
        return assessment

    logger.info(
        f"Creating new assessment for user {user.id} and objective {learning_objective.id}"
    )

    assessment, created = await sync_to_async(
        UserAssessmentAttempt.get_or_create_attempt
    )(user=user, learning_objective=learning_objective)

    if created:
        logger.info(f"Created new assessment {assessment.assessment_id}")
    else:
        logger.info(f"Retrieved existing assessment {assessment.assessment_id}")

    # setting assessment expiry
    assessment_data = AssessmentTimerData(
        assessment_id=assessment.assessment_id,
        student_id=user.id,
        started_at=datetime.now(),
        assessment_duration_seconds=600,  # defaulting to 10 min for now.but should create dynamic time depending on questions
    )

    scheduler_response = await schedule_test_assessment(data=assessment_data)
    if not scheduler_response:
        raise SchedulingError()

    return assessment
