import logging
from datetime import datetime

from django.db import transaction

from src.library.scheduler.assessment_scheduler import (
    AssessmentTimerData,
    schedule_test_assessment,
)
from src.utils.mixins.question_mixin import QuestionSetResources

from ..models import UserAssessmentAttempt

logger = logging.getLogger(__name__)


def start_assessment(
    *, resources_context: QuestionSetResources
) -> UserAssessmentAttempt:
    """
    Start or retrieve an active assessment for a user based on their learning objective.

    This function first checks if the user already has an active assessment for the given
    learning objective. If one exists, it returns that assessment. Otherwise, it creates
    a new assessment attempt and schedules it with a timer for expiration.

    Args:
        resources_context (ServiceResources): Context containing user and learning objective resources.

    Returns:
        UserAssessmentAttempt: The active or newly created assessment attempt.

    Raises:
        SchedulingError: If the assessment timer could not be scheduled.
    """
    user = resources_context.resources.user
    learning_objective = resources_context.resources.learning_objective

    logger.debug(
        f"Fetching active assessment for user {user.id} and objective {learning_objective.id}"
    )

    if assessment := UserAssessmentAttempt.get_active_attempt(
        user=user, learning_objective=learning_objective
    ):
        logger.info(
            f"Found existing active assessment {assessment.assessment_id} for user {user.id}"
        )
        return assessment

    logger.info(
        f"Creating new assessment for user {user.id} and objective {learning_objective.id}"
    )
    with transaction.atomic():
        assessment = UserAssessmentAttempt.create_attempt(
            user=user, learning_objective=learning_objective
        )

        logger.info(f"Created new assessment {assessment.assessment_id}")

        assessment_data = AssessmentTimerData(
            assessment_id=str(assessment.assessment_id),
            student_id=user.id,
            started_at=datetime.now(),
            assessment_duration_seconds=30,
            # defaulting to 30 sec for now, but should create dynamic time depending on questions
        )

        schedule_test_assessment(data=assessment_data)

        logger.info(
            f"Successfully scheduled timer for assessment {assessment.assessment_id}"
        )
        return assessment
