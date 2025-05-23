import logging

from rest_framework import status
from rest_framework.response import Response

from src.utils.mixins.context import EducationContextMixin
from src.utils.views.base import CustomRetrieveAPIView, CustomUpdateAPIView

from .exceptions import SchedulingError, UserQuestionSetNotFoundError
from .serializers import AssessmentSerializer
from .services.assessment_start_service import start_assessment
from .services.assessment_view_service import get_current_ongoing_assessment

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
    # TODO : to be implemented
    pass


class AssessmentStartView(EducationContextMixin, CustomRetrieveAPIView):
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
        education_context = self.get_validated_service_resources(serializer)
        try:
            assessment = start_assessment(education_context=education_context)
            return Response(
                data={"assessment_id": assessment.assessment_id},
                status=status.HTTP_200_OK,
            )

        except SchedulingError as e:
            return Response(
                data={"message": e.message},
                status=status.HTTP_408_REQUEST_TIMEOUT,
            )


class ActiveAssessmentView(EducationContextMixin, CustomRetrieveAPIView):
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
        education_context = self.get_validated_service_resources(serializer)

        try:
            assessment_data = get_current_ongoing_assessment(
                education_context=education_context
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
