import logging
import uuid

from rest_framework import status
from rest_framework.response import Response

from src.exceptions import SchedulingError, UserQuestionSetNotFoundError
from src.utils.mixins.question_mixin import QuestionSetMixin
from src.utils.views.base import CustomAPIView

from .serializers import AssessmentGradingSerializer, AssessmentSerializer
from .services.assessment_grader import grade_assessment
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
        except UserQuestionSetNotFoundError as e:
            return Response(e.to_dict(), status=status.HTTP_404_NOT_FOUND)


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
        except UserQuestionSetNotFoundError as e:
            return Response(e.to_dict(), status=status.HTTP_404_NOT_FOUND)
