import logging
import uuid

from rest_framework import status
from rest_framework.response import Response

from src.utils.mixins.question_mixin import QuestionSetMixin
from src.utils.views.base import CustomAPIView

from .exceptions import SchedulingError, UserQuestionSetNotFoundError
from .serializers import AssessmentGradingSerializer, AssessmentSerializer
from .services.assessment_grading.assessment_completion import grade_assessment
from .services.assessment_start_service import start_assessment
from .services.assessment_view_service import get_current_ongoing_assessment

logger = logging.getLogger(__name__)


class AssessmentCompletionView(QuestionSetMixin, CustomAPIView):
    serializer_class = AssessmentGradingSerializer

    async def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data={**request.data, "username": request.user.username}
        )
        resource_context = await self.get_validated_question_set_resources_async(
            serializer
        )
        try:
            grading_result = await grade_assessment(
                assessment_id=uuid.UUID(request.data["assessment_id"]),
                resources_context=resource_context,
            )

            return Response(grading_result.model_dump(), status=status.HTTP_200_OK)
        except UserQuestionSetNotFoundError:
            pass

        return Response(status=status.HTTP_200_OK)


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
            return Response(
                data={"message": e.message},
                status=status.HTTP_408_REQUEST_TIMEOUT,
            )


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
                    },
                    status=status.HTTP_200_OK,
                )

            return Response(
                data={
                    "assessment_id": None,
                    "has_active": False,
                    "num_questions": assessment_data.num_questions,
                },
                status=status.HTTP_200_OK,
            )
        except UserQuestionSetNotFoundError:
            return Response(
                data={
                    "message": "Unable to retrieve questions. Please contact support."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
