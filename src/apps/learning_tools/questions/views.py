import logging

from asgiref.sync import async_to_sync
from rest_framework import status
from rest_framework.response import Response

from src.utils.mixins.context import EducationContextMixin
from src.utils.views.base import CustomRetrieveAPIView, CustomUpdateAPIView

from .serializers import QuestionSerializer, UserQuestionAttemptSerializer
from .services.question_attempt_service import QuestionAttemptRecorder
from .services.question_list_service import get_question_attempts

log = logging.getLogger(__name__)


class QuestionsListView(EducationContextMixin, CustomRetrieveAPIView):
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
        serializer = self.get_serializer(data=kwargs)
        education_context = self.get_validated_service_resources(kwargs, serializer)
        question_data = education_context.resources.question_set_ids

        log.debug(
            "Got education context for user %s, block %s",
            education_context.validated_data.get("username"),
            education_context.validated_data.get("block_id"),
        )

        if not question_data:
            log.warning(
                "No valid question IDs found for user %s and block %s",
                education_context.validated_data["username"],
                education_context.validated_data["block_id"],
            )
            return Response(
                {
                    "message": f"No valid question IDs found for user {education_context.validated_data['username']}",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        log.info(
            "Successfully retrieved %d questions for user %s",
            len(question_data),
            education_context.validated_data["username"],
        )
        return Response(
            {
                "username": education_context.validated_data["username"],
                "block_id": education_context.validated_data["block_id"],
                "questions": question_data,
            },
            status=status.HTTP_200_OK,
        )


class QuestionAttemptListView(EducationContextMixin, CustomRetrieveAPIView):
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
        serializer = self.get_serializer(data=kwargs)
        education_context = await self.get_validated_service_resources_async(
            kwargs, serializer
        )
        question_attempts = await get_question_attempts(
            education_context=education_context
        )

        return Response(
            data={model.question_id: model.model_dump() for model in question_attempts},
            status=status.HTTP_200_OK,
        )


# TODO : catch and handle this error : QuestionNotFoundError
class QuestionAttemptsCreateView(EducationContextMixin, CustomUpdateAPIView):
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
            serializer = self.get_serializer(data=request.data)
            education_context = await self.get_validated_service_resources_async(
                request.data, serializer
            )
            question_recorder = QuestionAttemptRecorder.get_question_recorder(
                education_context
            )
            result = await question_recorder.record_assessment()

            return Response(
                {result.question_id: result.grading_result.to_dict()},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            log.error("Error processing question attempt: %s", str(e), exc_info=True)
            return Response(
                {"error": "An error occurred while processing your question attempt"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
