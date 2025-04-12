import logging

from bson import ObjectId
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_core.learning_mode_rules import LearningModeType
from ai_core.validator.validator_engine import ValidationEngine
from course_ware.models import Course, UserQuestionSet
from course_ware.serializers import PostQuestionAttemptSerializer
from course_ware.services.question_service import QuestionService
from data_types.questions import QuestionAttemptData
from edu_vault.settings.common import NO_SQL_DATABASE_NAME
from grade_book.grader import Gradebook
from grade_book.strategy import StandardLearningModeStrategy

from .models import EdxUser, SubTopic, UserQuestionAttempts
from .serializers import (GetSingleQuestionSerializer, QueryParamsSerializer,
                          UserQuestionAttemptSerializer)
from .services.question_attempt_service import QuestionAttemptService
from .utils import find_sequential_path, get_iframe_id_from_outline

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


class GetQuestionsView(CustomRetrieveAPIView):
    """
    API view to retrieve questions for a specific user and topic.

    This view fetches questions based on the provided username and block_id,
    with optional filtering by grading mode.
    """

    serializer_class = QueryParamsSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Override the retrieve method to implement our custom logic.
        """
        serializer = self.get_serializer(**kwargs)
        username = serializer.data.get("username")
        block_id = serializer.data.get("block_id")

        qn_service = QuestionService(serializer=serializer)
        resources = qn_service.get_resources()
        question_data = []

        if not resources.question_set_ids:
            log.info("No valid question IDs found for user %s", username)
            return Response(
                {
                    "message": f"No valid question IDs found for user {username}",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        grading_mode = qn_service.is_grading_mode()

        # Only fetch questions if not in grading mode
        if not grading_mode:
            question_data = qn_service.get_questions_from_ids()

        return Response(
            {
                "username": username,
                "block_id": block_id,
                "questions": question_data,
                "grading_mode": grading_mode,
            },
            status=status.HTTP_200_OK,
        )


class GetSingleQuestionAttemptView(CustomRetrieveAPIView):
    """
    API view to retrieve a single question attempt for a specific user.

    This view returns metadata about a user's attempt on a specific question,
    including correctness counts.
    """

    serializer_class = GetSingleQuestionSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Override the retrieve method to implement our custom logic.
        """
        # automatically validates the serializer
        serializer = self.get_serializer(**kwargs)
        question_id = serializer.data.get("question_id")

        qn_service = QuestionService(serializer=serializer)
        resources = qn_service.get_resources()

        user_question_attempt = get_object_or_404(
            UserQuestionAttempts, user=resources.user, sub_topic=resources.sub_topic
        )

        # Get metadata for this specific question
        response = user_question_attempt.get_latest_question_metadata.get(question_id)

        # Build response with summary counts
        total_correct = user_question_attempt.get_correct_questions_count
        total_incorrect = user_question_attempt.get_incorrect_questions_count

        if not response:
            # Question doesn't have an entry yet
            return Response(
                {
                    "total_correct_count": total_correct,
                    "total_incorrect_count": total_incorrect,
                },
                status=status.HTTP_200_OK,
            )

        # Return full question attempt data
        return Response(
            QuestionAttemptData(
                **response,
                total_correct_count=total_correct,
                total_incorrect_count=total_incorrect,
            ).model_dump(),
            status=status.HTTP_200_OK,
        )


class GetQuestionAttemptView(CustomRetrieveAPIView):
    """
    API view to retrieve all question attempts for a user and topic.

    This view returns a summary of all attempts made by a user for questions
    in a specific topic.
    """

    serializer_class = UserQuestionAttemptSerializer

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(**kwargs)
        username = serializer.data.get("username")
        block_id = serializer.data.get("block_id")
        user = get_object_or_404(EdxUser, username=username)
        sub_topic = get_object_or_404(SubTopic, block_id=block_id)

        attempt, created = UserQuestionAttempts.objects.get_or_create(
            user=user,
            sub_topic=sub_topic,
        )
        if created:
            log.info(
                "Created new UserQuestionAttempts for user %s, topic %s",
                username,
                block_id,
            )

        response_serializer = UserQuestionAttemptSerializer(attempt)
        return Response(response_serializer.data)


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

        except Exception as e:
            return Response(
                {"error": str(e), "status": "error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["GET"])
def iframe_id_given_topic_id(request, sub_topic_id: str) -> Response:
    # TODO : the doc string is written in Edx language, adapt it to
    # fit the current context
    """
    Get the first vertical (unit) ID for a given sequential (topic) ID.

    This function traverses the course outline structure to find the first vertical (unit)
    that is a child of the specified sequential (topic). This is used to determine which
    unit should be displayed in an iframe when accessing a topic.

    Args:
        request: The HTTP request object.
        sub_topic_id: The block_id (identifier) of the sequential/topic.

    Returns:
        Response: A response containing the iframe_id for the first vertical.

    Raises:
        Http404: If no vertical is found or if the sub_topic doesn't exist.

    Example URL:
        /api/iframe-id/block-v1:edX+DemoX+Demo_Course+type@sequential+block@12345/
    """

    # Retrieve the SubTopic object or return 404 if not found
    sub_topic = get_object_or_404(SubTopic, block_id=sub_topic_id)

    # Get the course outline from the associated course
    course = sub_topic.topic.course
    course_outline = course.course_outline

    if not course_outline:
        return Response(
            {"error": "Course outline is not available"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Find the iframe ID in the course outline
    iframe_id = get_iframe_id_from_outline(sub_topic_id, course_outline)

    if not iframe_id:
        raise Http404("No vertical found for this sequential")

    return Response({"iframe_id": iframe_id}, status=status.HTTP_200_OK)


class PostQuestionAttemptView(CustomUpdateAPIView):
    """Handle posting and processing of question attempts."""

    serializer_class = PostQuestionAttemptSerializer

    def post(self, request):

        serializer = self.get_serializer(**kwargs)

        qn_service = QuestionService(serializer=serializer)
        resources = qn_service.get_resources()

        user_question_attempt = get_object_or_404(
            UserQuestionAttempts, user=resources.user, sub_topic=resources.sub_topic
        )
        question_metadata = user_question_attempt.get_latest_question_metadata
        qn_attempt_service = QuestionAttemptService(
            collection_name=resources.collection_name,
            metadata=question_metadata,
            question_id=self.kwargs["question_id"],
            choice_id=self.kwargs["choice_id"],
            difficulty=self.kwargs["difficulty"],
            sub_topic_name=resources.sub_topic.name,
        )
        result = qn_attempt_service.process_question(user_question_attempt)
        return result


class QuizCompletionView(CustomUpdateAPIView):
    # TODO : one thing we need to implement is Authorization, Authentication and Auditing for the API endpoints
    """
    View to handle the completion of a quiz/challenge.
    """

    serializer_class = QueryParamsSerializer

    def _ensure_user_question_attempts_exist(
        self,
        user_question_ids: set[str],
        user_attempts_instance: UserQuestionAttempts,
        collection_name: str,
    ):
        """
        Ensures that all questions in the provided user_question_ids have corresponding attempt data.
        If attempt data is missing, it is created with default values.

        Args:
            user_question_ids (set[str]): Set of question IDs for the user.
            user_attempts_instance (UserQuestionAttempts): Instance containing user question attempts.
            collection_name (str): Name of the No SQL Database collection to fetch question data from.
        """

        existing_attempts = user_attempts_instance.get_latest_question_metadata

        missing_question_ids = user_question_ids - existing_attempts.keys()

        if not missing_question_ids:
            return

        question_data_list = self.no_sql_database_client.fetch_from_db(
            collection_name,
            NO_SQL_DATABASE_NAME,
            {
                "_id": {
                    "$in": [
                        ObjectId(question_id) for question_id in missing_question_ids
                    ]
                }
            },
        )

        fetched_question_ids = {
            str(question_data["_id"]) for question_data in question_data_list
        }

        missing_questions = missing_question_ids - fetched_question_ids
        if missing_questions:
            raise ValueError(
                f"Questions with IDs {', '.join(missing_questions)} not found in the database."
            )

        for question_data in question_data_list:
            question_id = str(question_data["_id"])
            question_instance = Question(**{**question_data, "_id": question_id})

            existing_attempts[question_id] = {
                "is_correct": False,
                "difficulty": question_instance.difficulty,
                "topic": question_instance.topic,
                "attempt_number": 0,
                "question_id": question_id,
            }

        user_attempts_instance.save()

    def post(self, request):

        serializer = self.get_serializer(**kwargs)

        qn_service = QuestionService(serializer=serializer)
        resources = qn_service.get_resources()

        user_question_attempt = get_object_or_404(
            UserQuestionAttempts, user=resources.user, sub_topic=resources.sub_topic
        )
        user_question_set = get_object_or_404(
            UserQuestionSet, user=resources.user, sub_topic=resources.sub_topic
        )

        learning_mode = LearningModeType.from_string(
            user_question_attempt.current_learning_mode
        )

        # we have to create a filler for all unattempted questions that the user has been assigned in the question set
        self._ensure_user_question_attempts_exist(
            question_set_ids, user_question_attempt, collection_name
        )

        # perform validation before we run grading process

        validator = ValidationEngine()

        validation_result = validator.run_all_validators(
            question_set=user_question_set,
            user_question_attempt_instance=user_question_attempt,
        )
        if validation_result:
            raise Exception(validation_result)

        performance_engine = create_performance_engine(
            user_id=user.id, topic_id=topic.id, learning_mode=learning_mode
        )
        performance_stats = performance_engine.get_topic_performance_stats()

        grader = Gradebook(
            topic=topic,
            user=user,
            user_attempt=user_question_attempt,
            user_question_set=user_question_set,
            learning_mode_strategy=StandardLearningModeStrategy(
                performance_stats=performance_stats,
                current_mode=user_question_attempt.current_learning_mode,
            ),
            performance_stats=performance_stats,
        )
        grade_data = grader.evaluate_performance()
        user_question_set.grading_mode = True
        user_question_set.save()

        # will run through celery
        # task_id = trigger_orchestration(
        #     user_id=user.id,
        #     question_metadata=user_question_attempt.get_latest_question_metadata,
        #     question_list_ids=list(user_question_set.get_question_set_ids),
        #     course_id=course.id,
        #     learning_mode=learning_mode,
        #     performance_stats=performance_stats,
        #     category_id=topic.category.id,
        #     topic_id=topic.id,
        #     block_id=str(topic.block_id),
        # )
        # print(task_id)

        return Response(
            grade_data.model_dump(),
            status=status.HTTP_201_CREATED,
        )
