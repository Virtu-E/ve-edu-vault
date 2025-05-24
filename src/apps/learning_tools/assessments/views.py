import logging

from rest_framework import status
from rest_framework.response import Response

from src.utils.mixins.question_mixin import QuestionSetMixin
from src.utils.views.base import CustomRetrieveAPIView, CustomUpdateAPIView

from .exceptions import SchedulingError, UserQuestionSetNotFoundError
from .serializers import AssessmentSerializer
from .services.assessment_start_service import start_assessment
from .services.assessment_view_service import get_current_ongoing_assessment

logger = logging.getLogger(__name__)


class AssessmentCompletionView(CustomUpdateAPIView):
    """
    View to handle the completion of a quiz/challenge.
    """

    serializer_class = AssessmentSerializer

    def retrieve(self, request, *args, **kwargs):
        """Main entry point for the assessment view."""
        pass


class AssessmentStartView(QuestionSetMixin, CustomRetrieveAPIView):
    """
    View to handle the start of an assessment.
    """

    serializer_class = AssessmentSerializer

    def retrieve(self, request, *args, **kwargs):
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


class ActiveAssessmentView(QuestionSetMixin, CustomRetrieveAPIView):
    """View that checks if the user has an active assessment."""

    serializer_class = AssessmentSerializer

    def retrieve(self, request, *args, **kwargs):
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
