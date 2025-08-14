import logging
import uuid

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from src.exceptions import (
    AssessmentAlreadyGradedError,
    SchedulingError,
    UserQuestionSetNotFoundError,
)
from src.utils.mixins.question_mixin import QuestionSetMixin
from src.utils.views.base import CustomAPIView

from .serializers import AssessmentGradingSerializer, AssessmentSerializer
from .services.assessment_grader import grade_assessment
from .services.assessment_start_service import start_assessment
from .services.assessment_view_service import (
    get_current_ongoing_assessment,
    get_individual_assessments,
    get_user_active_learning_assessment_overview,
)

logger = logging.getLogger(__name__)


class AssessmentCompletionView(QuestionSetMixin, CustomAPIView):
    serializer_class = AssessmentGradingSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data={**request.data, "username": request.user.username}
        )
        resource_context = self.get_validated_question_set_resources(serializer)
        try:
            with transaction.atomic():
                grading_result = grade_assessment(
                    assessment_id=uuid.UUID(request.data["assessment_id"]),
                    resources_context=resource_context,
                )

            return Response(grading_result.model_dump(), status=status.HTTP_200_OK)
        except UserQuestionSetNotFoundError as e:
            return Response(e.to_dict(), status=status.HTTP_404_NOT_FOUND)

        except AssessmentAlreadyGradedError as e:
            return Response(e.to_dict(), status=status.HTTP_400_BAD_REQUEST)


class AssessmentStartView(QuestionSetMixin, CustomAPIView):
    """
    View to handle the start of an assessment.
    """

    serializer_class = AssessmentSerializer

    def get(self, request, *args, **kwargs):
        """
        Main entry point for this view.
        """
        logger.info(f"Assessment start requested by user {request.user.username}")
        serializer = self.get_serializer(
            data={**kwargs, "username": request.user.username}
        )
        resources_context = self.get_validated_question_set_resources(serializer)
        try:
            assessment = start_assessment(resources_context=resources_context)
            return Response(
                data={"assessment_id": assessment.assessment_id},
                status=status.HTTP_200_OK,
            )

        except SchedulingError as e:
            return Response(data=e.to_dict(), status=status.HTTP_400_BAD_REQUEST)


class ActiveAssessmentView(QuestionSetMixin, CustomAPIView):
    """View that checks if the user has an active assessment."""

    serializer_class = AssessmentSerializer

    def get(self, request, *args, **kwargs):
        """
        Main entry point for this view.
        """
        logger.info(f"Active assessment check requested for {kwargs}")

        serializer = self.get_serializer(
            data={**kwargs, "username": request.user.username}
        )
        resources_context = self.get_validated_question_set_resources(serializer)

        try:
            assessment_data = get_current_ongoing_assessment(
                resources_context=resources_context,
            )
            if assessment_data.assessment:
                return Response(
                    data={
                        "assessment_id": assessment_data.assessment.assessment_id,
                        "has_active": True,
                        "num_questions": assessment_data.num_questions,
                        "questions_attempted": assessment_data.questions_attempted,
                    },
                    status=status.HTTP_200_OK,
                )

            return Response(
                data={
                    "assessment_id": None,
                    "has_active": False,
                    "num_questions": assessment_data.num_questions,
                    "questions_attempted": 0,
                },
                status=status.HTTP_200_OK,
            )
        except UserQuestionSetNotFoundError as e:
            return Response(e.to_dict(), status=status.HTTP_404_NOT_FOUND)


class AssessmentResultsView(QuestionSetMixin, CustomAPIView):
    """View that gets the users assessment results statistics."""

    serializer_class = AssessmentSerializer

    def get(self, request, *args, **kwargs):
        """
        Main entry point for getting user assessment statistics.
        """
        logger.info(f"Assessment statistics requested for {kwargs}")

        serializer = self.get_serializer(
            data={**kwargs, "username": request.user.username}
        )
        resources_context = self.get_validated_question_set_resources(serializer)

        try:
            stats_data = get_individual_assessments(
                resources_context=resources_context,
            )

            return Response(
                data=stats_data,
                status=status.HTTP_200_OK,
            )
        except UserQuestionSetNotFoundError as e:
            return Response(e.to_dict(), status=status.HTTP_404_NOT_FOUND)


class UserActiveAssessmentsOverviewView(QuestionSetMixin, CustomAPIView):
    """View that provides a comprehensive overview of all active assessments for a user."""

    serializer_class = AssessmentSerializer

    def get(self, request, *args, **kwargs):
        """
        Main entry point for getting user's active assessments overview.

        Returns a comprehensive view of all active learning assessments for the user,
        including progress information for each assessment.

        Response format:
        {
            "user_id": "123",
            "username": "student1",
            "total_active_assessments": 3,
            "has_active_assessments": true,
            "assessments": [
                {
                    "assessment_id": "uuid-123",
                    "assessment_name": "Math Fundamentals",
                    "learning_objective_name": "Math Fundamentals",
                    "started_at": "2025-07-20T10:30:00Z",
                    "total_questions": 20,
                    "questions_attempted": 15,
                    "progress_percentage": 75.0,
                    "is_complete": false
                }
            ]
        }
        """
        logger.info(f"User assessment overview requested for {kwargs}")

        try:
            assessment_overview_data = get_user_active_learning_assessment_overview(
                user=request.user
            )

            return Response(
                data=assessment_overview_data,
                status=status.HTTP_200_OK,
            )
        except UserQuestionSetNotFoundError as e:
            return Response(e.to_dict(), status=status.HTTP_404_NOT_FOUND)
