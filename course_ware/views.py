import logging
from typing import Any, Dict, Optional, Set, Tuple

from bson import ObjectId
from decouple import config
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_core.learning_mode_rules import LearningModeType, LearningRuleFactory
from ai_core.orchestration.orchestration_engine import OrchestrationEngine
from course_ware.mixins import RetrieveUserAndResourcesMixin
from course_ware.models import Course, EdxUser, Topic, UserQuestionAttempts, UserQuestionSet
from course_ware.serializers import GetSingleQuestionSerializer, PostQuestionAttemptSerializer, QueryParamsSerializer, UserQuestionAttemptSerializer
from data_types.questions import Question, QuestionAttemptData
from edu_vault.settings.common import NO_SQL_DATABASE_NAME
from exceptions import ParsingError, QuestionNotFoundError
from grade_book.grader import Gradebook
from grade_book.messages import ModeMessageGenerator
from grade_book.performance_evaluator import PerformanceEvaluator
from grade_book.strategy import StandardLearningModeStrategy
from no_sql_database.mongodb import mongo_database
from no_sql_database.nosql_database_engine import NoSqLDatabaseEngineInterface
from repository.grade_book import MongoLearningHistoryRepository

log = logging.getLogger(__name__)


class QuestionViewBase(RetrieveUserAndResourcesMixin, APIView):
    """Base class for all question views with common functionality."""

    serializer_class = None

    def __init__(self, **kwargs):
        super().__init__()
        if not self.serializer_class:
            raise Exception("serializer_class must be set on the view")
        self.serializer = None

    def validate_and_get_resources(self, data) -> Tuple[EdxUser, Topic, Set[str]]:
        """Common validation and resource retrieval logic."""
        self.serializer = self.serializer_class(data=data)
        if not self.serializer.is_valid():
            raise ValidationError(self.serializer.errors)

        user = self.get_user_from_validated_data(self.serializer)
        topic = self.get_topic_from_validated_data(self.serializer)
        user_question_set_instance = self.get_user_question_set(user, topic)

        return user, topic, user_question_set_instance.get_question_set_ids

    @staticmethod
    def validate_question_exists(question_id: str, question_set: set[str], username: str) -> bool:
        if question_id not in question_set:
            error_msg = f"Question ID '{question_id}' not found in question set for user '{username}'"
            log.error(error_msg)
            raise QuestionNotFoundError(question_id, username)
        return True

    @staticmethod
    def handle_response(func):
        """Decorator for handling common error responses."""

        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValidationError as e:
                log.error(str(e))
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except TypeError as e:
                log.error(f"Operation failed due to a TypeError: {str(e)}")
                return Response(
                    {
                        "error": "Invalid request",
                        "message": "Ensure all required parameters are included in the GET request.",
                        "details": str(e),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return wrapper


class DatabaseQuestionViewBase(QuestionViewBase):
    """Base class for views that require database access."""

    no_sql_database_client = None

    def __init__(self, **kwargs):
        super().__init__()
        self.no_sql_database_client = kwargs.get("no_sql_database_client")
        if not self.no_sql_database_client:
            raise ValueError("database_client is required")
        if not isinstance(self.no_sql_database_client, NoSqLDatabaseEngineInterface):
            raise ValueError("Please use a valid database engine instance")

    @staticmethod
    def _get_collection_name_from_topic(topic: Topic) -> str:
        if not isinstance(topic, Topic):
            log.error("Invalid topic instance")
            raise ValidationError("Invalid topic instance")

        course_id = topic.category.course.course_key
        collection_name = course_id
        if not collection_name:
            log.error(f"could not find database collection associated with the course ID {course_id}")
            raise ParsingError(f"could not find database collection associated with the course ID {course_id}")
        return collection_name

    def validate_and_get_resources(self, data) -> Tuple[EdxUser, Topic, Set[str], str]:
        """Extended validation that includes collection name."""
        user, topic, question_set_ids = super().validate_and_get_resources(data)
        collection_name = self._get_collection_name_from_topic(topic)
        return user, topic, question_set_ids, collection_name


class GetQuestionsView(DatabaseQuestionViewBase):
    """Get questions for a specific user and topic."""

    serializer_class = QueryParamsSerializer

    @QuestionViewBase.handle_response
    def get(self, request, username, block_id):
        user, topic, question_set_ids, collection_name = self.validate_and_get_resources(
            data=({"username": username, "block_id": block_id}),
        )

        object_ids = [ObjectId(id) for id in question_set_ids if ObjectId.is_valid(id)]

        if not object_ids:
            log.info(f"No valid question IDs found for user '{username}'")
            return Response(
                {"message": f"No valid question IDs found for user {username}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        docs = self.no_sql_database_client.fetch_from_db(collection_name, NO_SQL_DATABASE_NAME, {"_id": {"$in": object_ids}})

        questions = [Question(**{**doc, "_id": str(doc["_id"])}).model_dump(by_alias=True, exclude={"choices": {"is_correct"}}) for doc in docs]

        return Response({
            "username": self.serializer.validated_data["username"],
            "block_id": self.serializer.validated_data["block_id"],
            "questions": questions,
        })


class PostQuestionAttemptView(DatabaseQuestionViewBase):
    """Handle posting and processing of question attempts."""

    serializer_class = PostQuestionAttemptSerializer
    MAX_ATTEMPTS = config("MAX_QUESTION_ATTEMPTS", default=3, cast=int)

    def _handle_existing_attempt(self, metadata: Dict[str, Any]) -> Optional[Response]:
        """Handle logic for an existing question attempt."""
        if metadata["is_correct"]:
            return Response(
                {"message": "Question already correctly answered"},
                status=status.HTTP_409_CONFLICT,
            )

        if metadata["attempt_number"] >= self.MAX_ATTEMPTS:
            return Response(
                {"message": f"Maximum attempts ({self.MAX_ATTEMPTS}) reached"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        return None

    @staticmethod
    def _is_choice_correct(question_instance: Question, choice_id: int) -> bool:
        return question_instance.choices[choice_id].is_correct

    def _is_choice_answer_correct(self, choice_id: int, question_id: str, collection_name: str) -> bool:
        result_lists = self.no_sql_database_client.fetch_from_db(collection_name, NO_SQL_DATABASE_NAME, {"_id": ObjectId(question_id)})
        # TODO : simplify this by removing the need pf checking the data structure
        result = result_lists[0] if isinstance(result_lists, list) else result_lists
        question_instance = Question(**{**result, "_id": str(question_id)})
        return self._is_choice_correct(question_instance, choice_id)

    @staticmethod
    def _update_question_metadata(metadata: Dict[str, Any], is_correct: bool, attempt_number: int) -> Dict[str, Any]:
        """Update the metadata for a question attempt."""
        return {**metadata, "is_correct": is_correct, "attempt_number": attempt_number}

    @QuestionViewBase.handle_response
    def post(self, request):
        user, topic, question_set_ids, collection_name = self.validate_and_get_resources(request.data)

        question_id = self.serializer.validated_data["question_id"]
        self.validate_question_exists(question_id, question_set_ids, self.serializer.validated_data["username"])

        user_question_attempt = get_object_or_404(UserQuestionAttempts, user=user, topic=topic)
        question_metadata = user_question_attempt.get_latest_question_metadata
        question_metadata_instance = question_metadata.get(question_id)

        if question_metadata_instance:
            response = self._handle_existing_attempt(question_metadata_instance)
            if response:
                return response

            question_metadata[question_id] = self._update_question_metadata(
                question_metadata_instance,
                is_correct=self._is_choice_answer_correct(
                    self.serializer.validated_data["choice_id"],
                    self.serializer.validated_data["question_id"],
                    collection_name,
                ),
                attempt_number=question_metadata_instance["attempt_number"] + 1,
            )
        else:
            question_metadata[question_id] = {
                "is_correct": self._is_choice_answer_correct(
                    self.serializer.validated_data["choice_id"],
                    self.serializer.validated_data["question_id"],
                    collection_name,
                ),
                "attempt_number": 1,
                "difficulty": self.serializer.validated_data["difficulty"],
                "topic": topic.name,
                "question_id": question_id,
            }

        question_metadata[question_id]["choice_id"] = self.serializer.validated_data["choice_id"]
        user_question_attempt.save()

        return Response(
            QuestionAttemptData(
                **question_metadata[question_id],
                total_incorrect_count=user_question_attempt.get_incorrect_questions_count,
                total_correct_count=user_question_attempt.get_correct_questions_count,
            ).model_dump(),
            status=status.HTTP_201_CREATED,
        )


class GetSingleQuestionAttemptView(QuestionViewBase):
    """Retrieve a  question attempt for a user in regards to a single question ID"""

    serializer_class = GetSingleQuestionSerializer

    @QuestionViewBase.handle_response
    def get(self, request, username, block_id, question_id):
        user, topic, question_set_ids = self.validate_and_get_resources(
            data=({"username": username, "block_id": block_id, "question_id": question_id}),
        )

        question_id = self.serializer.validated_data["question_id"]
        self.validate_question_exists(question_id, question_set_ids, self.serializer.validated_data["username"])

        user_question_attempt = get_object_or_404(UserQuestionAttempts, user=user, topic=topic)
        response = user_question_attempt.get_latest_question_metadata.get(question_id)
        if not response:
            # means that the question does not yet have an entry in the question attempt metadata
            return Response({
                "total_correct_count": user_question_attempt.get_correct_questions_count,
                "total_incorrect_count": user_question_attempt.get_incorrect_questions_count,
            })

        return Response(
            QuestionAttemptData(
                **response,
                total_correct_count=user_question_attempt.get_correct_questions_count,
                total_incorrect_count=user_question_attempt.get_incorrect_questions_count,
            ).model_dump()
        )


class GetQuestionAttemptView(APIView):
    def get(self, request, username, block_id):
        user = get_object_or_404(EdxUser, username=username)
        topic = get_object_or_404(Topic, block_id=block_id)

        attempt, _ = UserQuestionAttempts.objects.get_or_create(
            user=user,
            topic=topic,
        )

        serializer = UserQuestionAttemptSerializer(attempt)
        return Response(serializer.data)


class QuizCompletionView(DatabaseQuestionViewBase):
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
            {"_id": {"$in": [ObjectId(question_id) for question_id in missing_question_ids]}},
        )

        fetched_question_ids = {str(question_data["_id"]) for question_data in question_data_list}

        missing_questions = missing_question_ids - fetched_question_ids
        if missing_questions:
            raise ValueError(f"Questions with IDs {', '.join(missing_questions)} not found in the database.")

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
        #   TODO : the naming here already shows that my function is doing two things. Change that
        user, topic, question_set_ids, collection_name = self.validate_and_get_resources(request.data)
        user_question_attempt = get_object_or_404(UserQuestionAttempts, user=user, topic=topic)
        user_question_set = get_object_or_404(UserQuestionSet, user=user, topic=topic)

        # we have to create a filler for all unattempted questions that the user has been assigned in the question set
        self._ensure_user_question_attempts_exist(question_set_ids, user_question_attempt, collection_name)

        learning_mode = LearningModeType.from_string(user_question_attempt.current_learning_mode)

        orchestration_engine = OrchestrationEngine(
            topic=topic,
            user=user,
            category=topic.category,
            course=topic.category.course,
            user_question_set=user_question_set,
            learning_mode=learning_mode,
            learning_mode_rule=LearningRuleFactory.create_rule(learning_mode),
            question_attempt=user_question_attempt,
        )
        performance_evaluator = PerformanceEvaluator(orchestration_engine=orchestration_engine)

        learning_history_repository = MongoLearningHistoryRepository(mongo_engine=mongo_database, database_name="", collection_name="")

        grader = Gradebook(
            topic=topic,
            user=user,
            user_attempt=user_question_attempt,
            user_question_set=user_question_set,
            performance_evaluator=performance_evaluator,
            message_generator=ModeMessageGenerator(),
            learning_mode_strategy=StandardLearningModeStrategy(),
            learning_history_repository=learning_history_repository,
        )
        grade_data = grader.evaluate_performance(user_question_attempt.current_learning_mode)

        print(grade_data.ai_recommendation)

        return Response(
            {
                "error": "Sequential block not found in course outline",
                "status": "error",
            },
            status=status.HTTP_201_CREATED,
        )


@api_view(["GET"])
def iframe_id_given_topic_id(request, topic_id):
    """
    Get the first vertical (unit) ID for a given sequential (topic) ID.
    """

    def _get_iframe_id_from_outline(topic_id, outline):
        course_structure = outline.get("course_structure", {})

        def find_sequential(structure):
            if structure.get("id") == topic_id:
                children = structure.get("child_info", {}).get("children", [])
                if children:
                    return children[0].get("id")
                return None

            child_info = structure.get("child_info", {})
            if child_info:
                children = child_info.get("children", [])
                for child in children:
                    result = find_sequential(child)
                    if result:
                        return result
            return None

        return find_sequential(course_structure)

    if request.method == "GET":
        topic = get_object_or_404(Topic, block_id=topic_id)
        course = topic.category.course
        course_outline = course.course_outline

        iframe_id = _get_iframe_id_from_outline(topic_id, course_outline)

        if not iframe_id:
            raise Http404("No vertical found for this sequential")

        return Response({"iframe_id": iframe_id})


class CourseOutlinePathView(APIView):
    """
    APIView to get the hierarchical path of a sequential block in a course outline
    Returns data in a nested dictionary structure by block category
    """

    def find_sequential_path(self, outline_data, sequential_id, current_path=None):
        """
        Recursively find the path to a sequential block in the course outline

        Args:
            outline_data (dict): Course outline data
            sequential_id (str): ID of the sequential block to find
            current_path (dict): Current path being built (used in recursion)

        Returns:
            dict: Dictionary containing block information organized by category
        """
        if current_path is None:
            current_path = {}

        if outline_data.get("id") and outline_data.get("display_name"):
            block_type = outline_data["category"]
            block_info = {
                "id": outline_data["id"],
                "name": outline_data["display_name"],
                "type": block_type,
            }
            current_path[block_type] = block_info

        if outline_data.get("id") == sequential_id:
            return current_path

        if outline_data.get("child_info") and outline_data["child_info"].get("children"):
            for child in outline_data["child_info"]["children"]:
                # Create a new dictionary for each recursive call
                new_path = current_path.copy()
                result = self.find_sequential_path(child, sequential_id, new_path)
                if result:
                    return result

        return None

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

            path = self.find_sequential_path(outline_data["course_structure"], sequential_id)

            if path:
                return Response({"path": path, "status": "success"})
            else:
                return Response(
                    {
                        "error": "Sequential block not found in course outline",
                        "status": "error",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        except Course.DoesNotExist:
            return Response(
                {"error": "Course not found", "status": "error"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": str(e), "status": "error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
