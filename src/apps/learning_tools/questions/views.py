import asyncio
import logging

from asgiref.sync import async_to_sync
from rest_framework import status
from rest_framework.response import Response

from src.services.grade_book_v2.question_grading.grading_response_service import (
    GradingResponseService,
)
from src.services.grade_book_v2.question_grading.qn_grading_service import (
    SingleQuestionGrader,
)
from src.services.grade_book_v2.question_grading.qn_grading_types import AttemptedAnswer
from src.utils.mixins.context import EducationContextMixin
from .serializers import QuestionSerializer, UserQuestionAttemptSerializer
from src.utils.views.base import CustomRetrieveAPIView, CustomUpdateAPIView
from ..assessments.util import get_assessment_id

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
        question_data = []

        log.debug(
            "Got education context for user %s, block %s",
            education_context.validated_data.get("username"),
            education_context.validated_data.get("block_id"),
        )

        if not education_context.resources.question_set_ids:
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
        question_service_bundle = await self.get_validated_service_resources_async(
            kwargs, serializer
        )

        user_id = question_service_bundle.resources.user.id
        collection_name = question_service_bundle.resources.collection_name
        log.debug(
            "Getting grading responses for user %s, collection %s",
            user_id,
            collection_name,
        )

        grading_response_service = GradingResponseService.get_service(
            collection_name=collection_name
        )

        try:
            assessment_id = await get_assessment_id(
                user=question_service_bundle.resources.user,
                learning_objective=question_service_bundle.resources.learning_objective,
            )
            log.debug("Got assessment ID %s for user %s", assessment_id, user_id)

            question_attempts = await grading_response_service.get_grading_responses(
                user_id=user_id,
                collection_name=collection_name,
                assessment_id=assessment_id,
            )
            log.info(
                "Retrieved %d question attempts for user %s",
                len(question_attempts),
                user_id,
            )

            return Response(
                data={
                    model.question_id: model.model_dump() for model in question_attempts
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            log.error("Error retrieving question attempts: %s", str(e), exc_info=True)
            return Response(
                {"error": "Failed to retrieve question attempts"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# TODO : catch and handle this error : QuestionNotFoundError
class QuestionAttemptsCreateView(EducationContextMixin, CustomUpdateAPIView):
    """
    View that handles a question attempt submission.

    This view processes student answers to questions, grades them using the appropriate grader,
    saves the attempt results, and returns the grading response.
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

        This method:
        1. Validates the request data
        2. Retrieves necessary resources
        3. Gets the appropriate grader
        4. Fetches the question and any existing attempt concurrently
        5. Grades the attempted answer
        6. Saves the attempt and grading response concurrently
        7. Returns the grading result

        Args:
            request: The HTTP request object
            **kwargs: Additional keyword arguments containing request data

        Returns:
            Response: HTTP response with grading results and 201 Created status
        """
        try:
            serializer = self.get_serializer(data=request.data)
            question_service_bundle = await self.get_validated_service_resources_async(
                request.data, serializer
            )

            question_id = question_service_bundle.validated_data["question_id"]
            user_id = question_service_bundle.resources.user.id
            collection_name = question_service_bundle.resources.collection_name

            log.debug(
                "Processing attempt for question %s by user %s", question_id, user_id
            )

            grader = SingleQuestionGrader.get_grader(collection_name)
            assessment_id = await get_assessment_id(
                user=question_service_bundle.resources.user,
                learning_objective=question_service_bundle.resources.learning_objective,
            )
            log.debug("Using assessment ID %s", assessment_id)

            try:
                question, question_attempt = await asyncio.gather(
                    question_service_bundle.service.get_question_by_id(question_id),
                    grader.get_question_attempt(
                        user_id=user_id,
                        question_id=question_id,
                        assessment_id=assessment_id,
                    ),
                )
                log.debug("Successfully fetched question and existing attempt")
            except Exception as e:
                log.error(
                    "Error fetching question or attempt: %s", str(e), exc_info=True
                )
                raise

            attempted_answer = AttemptedAnswer(
                question_type=question_service_bundle.validated_data["question_type"],
                question_metadata=question_service_bundle.validated_data[
                    "question_metadata"
                ],
            )

            log.debug("Grading question attempt for question %s", question_id)
            grading_result = grader.grade(
                user_id=user_id,
                attempted_answer=attempted_answer,
                question=question,
                question_attempt=question_attempt,
            )

            grading_response_service = GradingResponseService.get_service(
                collection_name=collection_name
            )

            if grading_result.success:
                log.debug(
                    "Saving successful attempt for question %s, correct: %s, score: %s",
                    question_id,
                    grading_result.is_correct,
                    grading_result.score,
                )
                await asyncio.gather(
                    grader.save_attempt(
                        user_id=user_id,
                        question=question,
                        is_correct=grading_result.is_correct,
                        score=grading_result.score,
                        assessment_id=assessment_id,
                        question_attempt=question_attempt,
                    ),
                    grading_response_service.save_grading_response(
                        user_id=user_id,
                        question_id=question_id,
                        assessment_id=assessment_id,
                        grading_response=grading_result,
                        question_type=question.question_type,
                    ),
                )
                log.info(
                    "Successfully processed and saved attempt for question %s by user %s",
                    question_id,
                    user_id,
                )
            else:
                log.warning(
                    "Question attempt for %s was not successful: %s",
                    question_id,
                    grading_result.feedback,
                )

            return Response(
                {question.id: grading_result.to_dict()},
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            log.error("Error processing question attempt: %s", str(e), exc_info=True)
            return Response(
                {"error": "An error occurred while processing your question attempt"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
