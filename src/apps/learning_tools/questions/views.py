import logging

from asgiref.sync import async_to_sync
from rest_framework import status
from rest_framework.response import Response

from src.utils.mixins.question_mixin import QuestionSetMixin
from src.utils.views.base import CustomRetrieveAPIView, CustomUpdateAPIView

from .exceptions import (
    GradingError,
    MaximumAttemptsError,
    QuestionAttemptError,
    QuestionNotFoundError,
)
from .serializers import QuestionSerializer, UserQuestionAttemptSerializer
from .services.attempt_recorder_service import QuestionAttemptRecorder
from .services.grading_service import get_graded_responses
from .services.question_service import QuestionService

log = logging.getLogger(__name__)


class QuestionsListView(QuestionSetMixin, CustomRetrieveAPIView):
    """
    API view to retrieve questions for a specific user and learning_objective.

    This view fetches questions based on the provided username and block_id,
    with optional filtering by grading mode.
    """

    serializer_class = QuestionSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Override the retrieve method to implement our custom logic.
        """
        log.info("Retrieving questions list with params: %s", kwargs)
        serializer = self.get_serializer(
            data={**kwargs, "username": request.user.username}
        )
        resource_context = self.get_validated_question_set_resources(serializer)
        question_set_ids = resource_context.resources.question_set_ids
        question_service = QuestionService.get_service(
            resource_context=resource_context
        )
        question_data = async_to_sync(question_service.get_questions_from_ids)(
            question_set_ids
        )

        log.debug(
            "Got education context for user %s, block %s",
            resource_context.validated_data.get("username"),
            resource_context.validated_data.get("block_id"),
        )

        if not question_data:
            log.warning(
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

        log.info(
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


class QuestionAttemptListView(QuestionSetMixin, CustomRetrieveAPIView):
    """
    API view to retrieve all question attempts for a user and learning_objective.

    This view returns a summary of all attempts made by a user for questions
    in a specific learning objective.
    """

    serializer_class = QuestionSerializer

    def retrieve(self, request, *args, **kwargs):
        log.info("Retrieving question attempts with params: %s", kwargs)
        return async_to_sync(self._async_retrieve)(request, *args, **kwargs)

    async def _async_retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data={**kwargs, "username": request.user.username}
        )
        resource_context = await self.get_validated_question_set_resources_async(
            serializer
        )
        question_attempts = await get_graded_responses(
            resource_context=resource_context
        )

        return Response(
            data={model.question_id: model.model_dump() for model in question_attempts},
            status=status.HTTP_200_OK,
        )


class QuestionAttemptsCreateView(QuestionSetMixin, CustomUpdateAPIView):
    """
    View that handles a question attempt submission.
    """

    serializer_class = UserQuestionAttemptSerializer

    def post(self, request, **kwargs):
        """
        Handle POST requests by delegating to the async implementation.

        Args:
            request: The HTTP request object
            **kwargs: Additional keyword arguments passed to the view

        Returns:
            Response: The HTTP response containing grading results
        """
        log.info("Received question attempt submission")
        return async_to_sync(self._async_post)(request, **kwargs)

    async def _async_post(self, request, **kwargs):
        """
        Asynchronous implementation of the POST request handler.
        """
        try:
            serializer = self.get_serializer(
                data={**request.data, "username": request.user.username}
            )
            resource_context = await self.get_validated_question_set_resources_async(
                serializer
            )
            question_recorder = QuestionAttemptRecorder.create_recorder(
                resource_context=resource_context
            )
            result = await question_recorder.record_attempt()

            return Response(
                {result.question_id: result.grading_result.to_dict()},
                status=status.HTTP_201_CREATED,
            )
        except QuestionNotFoundError as e:
            log.error(f"Question not found: {e}")
            raise
        except MaximumAttemptsError as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except GradingError as e:
            log.error(f"Grading failed: {e}")
            raise
        except QuestionAttemptError as e:
            log.error(f"General error: {e}")
            raise
