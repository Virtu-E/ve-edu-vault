import asyncio
import logging
from datetime import datetime

from asgiref.sync import async_to_sync, sync_to_async
from rest_framework import status
from rest_framework.response import Response

from src.apps.learning_tools.assessments.models import UserAssessmentAttempt
from src.apps.learning_tools.questions.models import UserQuestionSet
from src.services.quiz_countdown.main import (
    AssessmentTimerData,
    schedule_test_assessment,
)
from src.utils.mixins.context import EducationContextMixin
from src.utils.views.base import CustomRetrieveAPIView, CustomUpdateAPIView

from .serializers import AssessmentSerializer

logger = logging.getLogger(__name__)


async def assessment_expiry_view(request):
    pass


class AssessmentExpiryView(CustomUpdateAPIView):

    def post(self, request, **kwargs):
        pass


class AssessmentCompletionView(CustomUpdateAPIView):
    # TODO : one thing we need to implement is Authorization, Authentication and Auditing for the API endpoints
    """
    View to handle the completion of a quiz/challenge.
    """

    serializer_class = AssessmentSerializer

    def update(self, request, *args, **kwargs):
        logger.info(
            f"Assessment completion initiated by user {request.user.id if hasattr(request, 'user') and request.user else 'unknown'}"
        )
        response = super().update(request, *args, **kwargs)
        logger.info(
            f"Assessment completion finished with status {response.status_code}"
        )
        return response


class AssessmentStartView(EducationContextMixin, CustomRetrieveAPIView):
    """
    View to handle the start of an assessment.
    """

    serializer_class = AssessmentSerializer

    def retrieve(self, request, *args, **kwargs):
        logger.info(
            f"Assessment start requested by user {request.user.id if hasattr(request, 'user') and request.user else 'unknown'}"
        )
        return async_to_sync(self._async_retrieve)(request, *args, **kwargs)

    async def _async_retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=kwargs)
        education_context = await self.get_validated_service_resources_async(
            request.data, serializer
        )
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
            return Response(
                data={"assessment_id": assessment.assessment_id},
                status=status.HTTP_200_OK,
            )

        logger.info(
            f"Creating new assessment for user {user.id} and objective {learning_objective.id}"
        )
        assessment, created = await sync_to_async(
            UserAssessmentAttempt.get_or_create_attempt
        )(user=user, learning_objective=learning_objective)

        # setting assessment expiry
        assessment_data = AssessmentTimerData(
            assessment_id=assessment.assessment_id,
            student_id=user.id,
            started_at=datetime.now(),
            assessment_duration_seconds=600,  # defaulting to 10 min for now.but should create dynamic time depending on questions
        )

        scheduler_response = await schedule_test_assessment(data=assessment_data)
        if not scheduler_response:
            return Response(
                data={
                    "message": "Failed to schedule assessment. Please try again later."
                },
                status=status.HTTP_408_REQUEST_TIMEOUT,
            )

        if created:
            logger.info(f"Created new assessment {assessment.assessment_id}")
        else:
            logger.info(f"Retrieved existing assessment {assessment.assessment_id}")

        return Response(
            data={"assessment_id": assessment.assessment_id},
            status=status.HTTP_200_OK,
        )


class ActiveAssessmentView(EducationContextMixin, CustomRetrieveAPIView):
    """View that checks if the user has an active assessment."""

    serializer_class = AssessmentSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Synchronous entry point that delegates to the async implementation.
        """
        logger.info(f"Active assessment check requested for {kwargs}")
        return async_to_sync(self._async_retrieve)(request, *args, **kwargs)

    async def _async_retrieve(self, request, *args, **kwargs):
        """
        Asynchronous implementation that fetches assessment data concurrently.
        """
        serializer = self.get_serializer(data=kwargs)
        education_context = await self.get_validated_service_resources_async(
            kwargs, serializer
        )

        user = education_context.resources.user
        learning_objective = education_context.resources.learning_objective

        logger.debug(
            f"Fetching assessment data for user {user.id} and objective {learning_objective.id}"
        )

        try:
            assessment, assessment_questions = await asyncio.gather(
                sync_to_async(UserAssessmentAttempt.get_active_attempt)(
                    user=user, learning_objective=learning_objective
                ),
                sync_to_async(UserQuestionSet.objects.get)(
                    user=user, learning_objective=learning_objective
                ),
            )
            logger.debug(f"Successfully gathered assessment data for user {user.id}")
        except UserQuestionSet.DoesNotExist:
            logger.warning(
                f"No question set found for user {user.id} and objective {learning_objective.id}"
            )
            return Response(
                {
                    "error": "No question set found for this user and learning objective."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        num_questions = len(list(assessment_questions.question_list_ids))

        if assessment:
            logger.info(
                f"Found active assessment {assessment.assessment_id} with {num_questions} questions"
            )
            return Response(
                data={
                    "assessment_id": assessment.assessment_id,
                    "has_active": True,
                    "num_questions": num_questions,
                },
                status=status.HTTP_200_OK,
            )

        logger.info(
            f"No active assessment found for user {user.id}, returning {num_questions} questions"
        )
        return Response(
            data={
                "assessment_id": None,
                "has_active": False,
                "num_questions": num_questions,
            },
            status=status.HTTP_200_OK,
        )
