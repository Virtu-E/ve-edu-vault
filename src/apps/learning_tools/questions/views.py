import logging

from rest_framework import status
from rest_framework.response import Response

from src.exceptions import QuestionNotFoundError, MaximumAttemptsExceededError
from src.utils.mixins.question_mixin import QuestionSetMixin
from src.utils.views.base import CustomAPIView

from .serializers import QuestionSerializer, UserQuestionAttemptSerializer
from .services.graded_responses import get_graded_responses_for_current_assessment
from .services.question_fetch_service import fetch_student_questions
from .services.question_grader.qn_grading_service import grade_student_submission

logger = logging.getLogger(__name__)


class StudentQuestionSetView(QuestionSetMixin, CustomAPIView):
    """API view to retrieve questions for a specific student and learning_objective."""

    serializer_class = QuestionSerializer

    def get(self, request, *args, **kwargs):
        """
        Override the retrieve method to implement our custom logic.
        """
        logger.info("Retrieving questions list with params: %s", kwargs)
        serializer = self.get_serializer(
            data={**kwargs, "username": request.user.username}
        )
        resource_context = self.get_validated_question_set_resources(serializer)
        question_data = fetch_student_questions(resource_context=resource_context)

        logger.debug(
            "Got education context for user %s, block %s",
            resource_context.validated_data.get("username"),
            resource_context.validated_data.get("block_id"),
        )

        if not question_data:
            logger.warning(
                "No valid question IDs found for user %s and block %s",
                resource_context.validated_data["username"],
                resource_context.validated_data["block_id"],
            )
            return Response(
                {
                    "message": f"No valid question IDs found for user {resource_context.validated_data['username']}",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        logger.info(
            "Successfully retrieved %d questions for user %s",
            len(question_data),
            resource_context.validated_data["username"],
        )
        return Response(
            {
                "username": resource_context.validated_data["username"],
                "block_id": resource_context.validated_data["block_id"],
                "questions": question_data,
            },
            status=status.HTTP_200_OK,
        )


class QuestionAttemptListView(QuestionSetMixin, CustomAPIView):
    """
    API view to retrieve all question attempts for a user and learning_objective.

    This view returns a summary of all attempts made by a user for questions
    in a specific learning objective.
    """

    serializer_class = QuestionSerializer

    async def get(self, request, *args, **kwargs):
        logger.info("Retrieving question attempts with params: %s", kwargs)

        serializer = self.get_serializer(
            data={**kwargs, "username": request.user.username}
        )
        resource_context = await self.get_validated_question_set_resources_async(
            serializer
        )
        question_attempts = await get_graded_responses_for_current_assessment(
            resource_context=resource_context,

        )

        return Response(
            data={model.question_id: model.model_dump() for model in question_attempts},
            status=status.HTTP_200_OK,
        )


class QuestionAttemptsCreateView(QuestionSetMixin, CustomAPIView):
    """View that handles a question attempt submission."""

    serializer_class = UserQuestionAttemptSerializer

    async def post(self, request, **kwargs):
        """Asynchronous implementation of the POST request handler."""
        logger.info("Received question attempt submission")

        try:
            serializer = self.get_serializer(
                data={**request.data, "username": request.user.username}
            )
            resource_context = await self.get_validated_question_set_resources_async(
                serializer
            )
            result = await grade_student_submission(resource_context=resource_context)

            return Response(
                {result.question_id: result.model_dump()},
                status=status.HTTP_201_CREATED,
            )
        except QuestionNotFoundError as e:
            logger.error(f"Question not found: {e}")
            return Response(
                e.to_dict(),
                status=status.HTTP_404_NOT_FOUND,
            )

        except MaximumAttemptsExceededError as e:
            return Response(e.to_dict(), status=status.HTTP_400_BAD_REQUEST)

