import asyncio
import logging

from asgiref.sync import async_to_sync, sync_to_async
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from course_ware.models import Course, UserAssessmentAttempt, UserQuestionSet
from course_ware.serializers import (
    PostQuestionAttemptSerializer,
    UserQuestionAttemptSerializer,
)
from grade_book_v2.question_grading.grading_response_service import (
    GradingResponseService,
)
from grade_book_v2.question_grading.qn_grading_service import SingleQuestionGrader
from grade_book_v2.question_grading.qn_grading_types import AttemptedAnswer
from oauth_clients.edx_client import EdxClient
from oauth_clients.services import OAuthClient

from .mixins import QuestionServiceMixin
from .serializers import QueryParamsSerializer
from .services.edx_content_service import EdxContentManager
from .services.util import get_assessment_id
from .utils import find_sequential_path

log = logging.getLogger(__name__)


class CustomRetrieveAPIView(RetrieveAPIView):
    """
    Custom RetrieveAPIView that overrides the get_object method.

    This view is designed for cases where standard object retrieval
    logic is not needed, allowing for custom response generation without
    relying on a database object.
    """

    def get_object(self):
        """
        Override the default get_object method.

        Returns:
            None: No object retrieval is performed.
        """
        return None


class CustomUpdateAPIView(UpdateAPIView):
    """Custom UpdateAPIView that overrides the get_object method."""

    def get_object(self):
        """
        Override the default get_object method.

        Returns:
            None: No object retrieval is performed.
        """
        return None


class GetQuestionsView(QuestionServiceMixin, CustomRetrieveAPIView):
    """
    API view to retrieve questions for a specific user and learning_objective.

    This view fetches questions based on the provided username and block_id,
    with optional filtering by grading mode.
    """

    serializer_class = QueryParamsSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Override the retrieve method to implement our custom logic.
        """
        serializer = self.get_serializer(data=kwargs)
        question_service_bundle = self.get_validated_service_resources(
            kwargs, serializer
        )
        question_data = []

        if not question_service_bundle.resources.question_set_ids:
            log.info(
                "No valid question IDs found for user %s",
                question_service_bundle.validated_data["username"],
            )
            return Response(
                {
                    "message": f"No valid question IDs found for user {question_service_bundle.validated_data['username']}",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        grading_mode = question_service_bundle.service.is_grading_mode()

        # Only fetch questions if not in grading mode
        if not grading_mode:
            question_data = async_to_sync(
                question_service_bundle.service.get_questions_from_ids
            )()

        return Response(
            {
                "username": question_service_bundle.validated_data["username"],
                "block_id": question_service_bundle.validated_data["block_id"],
                "questions": question_data,
                "grading_mode": grading_mode,
            },
            status=status.HTTP_200_OK,
        )


class GetQuestionAttemptView(QuestionServiceMixin, CustomRetrieveAPIView):
    """
    API view to retrieve all question attempts for a user and learning_objective.

    This view returns a summary of all attempts made by a user for questions
    in a specific learning objective.
    """

    serializer_class = UserQuestionAttemptSerializer

    def retrieve(self, request, *args, **kwargs):
        return async_to_sync(self._async_retrieve)(request, *args, **kwargs)

    async def _async_retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=kwargs)
        question_service_bundle = await self.get_validated_service_resources_async(
            kwargs, serializer
        )

        grading_response_service = GradingResponseService.get_service(
            collection_name=question_service_bundle.resources.collection_name
        )

        assessment_id = await get_assessment_id(
            user=question_service_bundle.resources.user,
            learning_objective=question_service_bundle.resources.learning_objective,
        )
        question_attempts = await grading_response_service.get_grading_responses(
            user_id=question_service_bundle.resources.user.id,
            collection_name=question_service_bundle.resources.collection_name,
            assessment_id=assessment_id,
        )

        return Response(
            data={model.question_id: model.model_dump() for model in question_attempts},
            status=status.HTTP_200_OK,
        )


class CourseOutlinePathView(APIView):
    """
    APIView to get the hierarchical path of a sequential block in a course outline
    Returns data in a nested dictionary structure by block category
    """

    def get(self, request, course_id, sequential_id):
        """
        GET handler to retrieve the path to a sequential block

        Args:
            course_id (str): ID of the course
            sequential_id (str): ID of the sequential block

        Returns:
            Response: Path information as nested dictionaries or error message
        """
        try:
            course = get_object_or_404(Course, course_key=course_id)
            outline_data = course.course_outline

            path = find_sequential_path(outline_data["course_structure"], sequential_id)

            if not path:
                return Response(
                    {
                        "error": "Sequential block not found in course outline",
                        "status": "error",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            return Response({"path": path, "status": "success"})

        except KeyError as e:
            return Response(
                {"error": str(e), "status": "error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# TODO : catch and handle this error : QuestionNotFoundError
class PostQuestionAttemptView(QuestionServiceMixin, CustomUpdateAPIView):
    """
    View that handles a question attempt submission.

    This view processes student answers to questions, grades them using the appropriate grader,
    saves the attempt results, and returns the grading response.
    """

    serializer_class = PostQuestionAttemptSerializer

    def post(self, request, **kwargs):
        """
        Handle POST requests by delegating to the async implementation.

        Args:
            request: The HTTP request object
            **kwargs: Additional keyword arguments passed to the view

        Returns:
            Response: The HTTP response containing grading results
        """
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
        serializer = self.get_serializer(data=request.data)
        question_service_bundle = await self.get_validated_service_resources_async(
            request.data, serializer
        )

        question_id = question_service_bundle.validated_data["question_id"]

        grader = SingleQuestionGrader.get_grader(
            question_service_bundle.resources.collection_name
        )
        assessment_id = await get_assessment_id(
            user=question_service_bundle.resources.user,
            learning_objective=question_service_bundle.resources.learning_objective,
        )

        question, question_attempt = await asyncio.gather(
            question_service_bundle.service.get_question_by_id(question_id),
            grader.get_question_attempt(
                user_id=question_service_bundle.resources.user.id,
                question_id=question_id,
                assessment_id=assessment_id,
            ),
        )

        attempted_answer = AttemptedAnswer(
            question_type=question_service_bundle.validated_data["question_type"],
            question_metadata=question_service_bundle.validated_data[
                "question_metadata"
            ],
        )

        grading_result = grader.grade(
            user_id=question_service_bundle.resources.user.id,
            attempted_answer=attempted_answer,
            question=question,
            question_attempt=question_attempt,
        )

        grading_response_service = GradingResponseService.get_service(
            collection_name=question_service_bundle.resources.collection_name
        )
        if grading_result.success:
            await asyncio.gather(
                grader.save_attempt(
                    user_id=question_service_bundle.resources.user.id,
                    question=question,
                    is_correct=grading_result.is_correct,
                    score=grading_result.score,
                    assessment_id=assessment_id,
                    question_attempt=question_attempt,
                ),
                grading_response_service.save_grading_response(
                    user_id=question_service_bundle.resources.user.id,
                    question_id=question_id,
                    assessment_id=assessment_id,
                    grading_response=grading_result,
                    question_type=question.question_type,
                ),
            )

        return Response(
            {question.id: grading_result.to_dict()},
            status=status.HTTP_201_CREATED,
        )


class AssessmentCompletionView(CustomUpdateAPIView):
    # TODO : one thing we need to implement is Authorization, Authentication and Auditing for the API endpoints
    """
    View to handle the completion of a quiz/challenge.
    """

    serializer_class = QueryParamsSerializer


class AssessmentStartView(QuestionServiceMixin, CustomRetrieveAPIView):
    """
    View to handle the start of an assessment.
    """

    serializer_class = QueryParamsSerializer

    def retrieve(self, request, *args, **kwargs):
        return async_to_sync(self._async_retrieve)(request, *args, **kwargs)

    async def _async_retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=kwargs)
        question_service_bundle = await self.get_validated_service_resources_async(
            request.data, serializer
        )
        user = question_service_bundle.resources.user
        learning_objective = question_service_bundle.resources.learning_objective

        if assessment := await sync_to_async(UserAssessmentAttempt.get_active_attempt)(
            user=user, learning_objective=learning_objective
        ):
            return Response(
                data={"assessment_id": assessment.assessment_id},
                status=status.HTTP_200_OK,
            )

        assessment, _ = await sync_to_async(
            UserAssessmentAttempt.get_or_create_attempt
        )(user=user, learning_objective=learning_objective)

        return Response(
            data={"assessment_id": assessment.assessment_id},
            status=status.HTTP_200_OK,
        )


class HasActiveAssessmentView(QuestionServiceMixin, CustomRetrieveAPIView):
    """View that checks if the user has an active assessment."""

    serializer_class = QueryParamsSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Synchronous entry point that delegates to the async implementation.
        """
        return async_to_sync(self._async_retrieve)(request, *args, **kwargs)

    async def _async_retrieve(self, request, *args, **kwargs):
        """
        Asynchronous implementation that fetches assessment data concurrently.
        """
        serializer = self.get_serializer(data=kwargs)
        question_service_bundle = await self.get_validated_service_resources_async(
            kwargs, serializer
        )

        user = question_service_bundle.resources.user
        learning_objective = question_service_bundle.resources.learning_objective

        try:
            assessment, assessment_questions = await asyncio.gather(
                sync_to_async(UserAssessmentAttempt.get_active_attempt)(
                    user=user, learning_objective=learning_objective
                ),
                sync_to_async(UserQuestionSet.objects.get)(
                    user=user, learning_objective=learning_objective
                ),
            )
        except UserQuestionSet.DoesNotExist:
            return Response(
                {
                    "error": "No question set found for this user and learning objective."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        num_questions = len(list(assessment_questions.question_list_ids))

        if assessment:
            return Response(
                data={
                    "assessment_id": assessment.assessment_id,
                    "has_active": True,
                    "num_questions": num_questions,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            data={
                "assessment_id": None,
                "has_active": False,
                "num_questions": num_questions,
            },
            status=status.HTTP_200_OK,
        )


async def get_learning_objectives(request, block_id=None):
    """
    Async Django view to get vertical blocks for a specified block ID

    Args:
        request: The HTTP request
        block_id: The EdX block ID

    Returns:
        JsonResponse with the vertical blocks data
    """
    if not block_id:
        block_id = request.GET.get("block_id")

    if not block_id:
        return JsonResponse({"error": "Block ID is required"}, status=400)

    # Get the EdX client and fetch course blocks
    async with OAuthClient(service_type="OPENEDX") as client:
        edx_client = EdxClient(client=client)
        blocks_data = await edx_client.get_course_blocks(block_id)

    if not blocks_data or "blocks" not in blocks_data:
        return JsonResponse(
            [],
            status=404,
        )

    # Extract only vertical blocks
    vertical_blocks = []

    for block_id, block_data in blocks_data["blocks"].items():
        if block_data.get("type") == "vertical":
            vertical_block = {
                "name": block_data.get("display_name", "Untitled"),
                "iframe_id": block_data.get("id"),
            }
            vertical_blocks.append(vertical_block)

    if not vertical_blocks:
        return JsonResponse(
            [],
            status=404,
        )

    return JsonResponse(vertical_blocks, safe=False)


async def get_edx_content_view(request, block_id):
    """
    Async Django view to get EdX content (HTML, PDF, Video) for a block ID

    Args:
        request: The HTTP request
        block_id: The EdX block ID

    Returns:
        JsonResponse with the content data
    """
    ordered = request.GET.get("ordered", "false").lower() == "true"

    # TODO : this is a bottle neck--> creating new connections on every new request
    # Use pooling
    # Get the EdX client and fetch course blocks
    async with OAuthClient(service_type="OPENEDX") as client:
        edx_client = EdxClient(client=client)
        blocks_data = await edx_client.get_course_blocks(block_id)

    content_manager = EdxContentManager(blocks_data)

    if not content_manager.valid:
        return JsonResponse(
            {
                "success": False,
                "message": "No content found",
                "content": {"html": [], "pdf": [], "video": []} if not ordered else [],
                "counts": {"html": 0, "pdf": 0, "video": 0},
            }
        )

    if ordered:
        content = content_manager.format_ordered_content()
    else:
        content = content_manager.format_categorized_content()

    counts = content_manager.get_content_counts(content)

    result = {
        "success": True,
        "block_id": block_id,
        "content": content,
        "counts": counts,
    }

    return JsonResponse(result)
