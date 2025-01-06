import logging
from typing import Any, Dict, Optional, Set, Tuple

from bson import ObjectId
from decouple import config
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from course_ware.mixins import RetrieveUserAndResourcesMixin
from course_ware.models import Topic, User, UserQuestionAttempts
from course_ware.serializers import (
    GetQuestionSerializer,
    PostQuestionAttemptSerializer,
    QueryParamsSerializer,
)
from data_types.questions import Question, QuestionAttemptData
from edu_vault.settings import common
from edu_vault.settings.common import COURSE_DATABASE_NAME_MAPPING, NO_SQL_DATABASE_NAME
from exceptions import ParsingError, QuestionNotFoundError
from nosql_database_engine import MongoDatabaseEngine, NoSqLDatabaseEngineInterface

log = logging.getLogger(__name__)


class QuestionManagementBase(RetrieveUserAndResourcesMixin, APIView):
    """
    Base class for question management views with common functionality.
    """

    serializer_class = None
    no_sql_database_client = None

    def __init__(self, **kwargs):
        super().__init__()
        self.no_sql_database_client = kwargs.get("no_sql_database_client")
        if not self.no_sql_database_client:
            raise ValueError("database_client is required")
        if not isinstance(self.no_sql_database_client, NoSqLDatabaseEngineInterface):
            raise ValueError("Please use a valid database engine instance")
        if not self.serializer_class:
            raise Exception("serializer_class must be set on the view")
        self.serializer = None

    # TODO : add validation for the database name here

    @staticmethod
    def _get_collection_name_from_topic(topic: Topic) -> str:
        if not isinstance(topic, Topic):
            log.error("Invalid topic instance")
            raise ValidationError("Invalid topic instance")

        course_id = topic.category.course.course_key

        collection_name = COURSE_DATABASE_NAME_MAPPING.get(course_id, None)
        if not collection_name:
            log.error(
                f"could not find database collection associated with the course ID {course_id}"
            )
            raise ParsingError(
                f"could not find database collection associated with the course ID {course_id}"
            )

        return collection_name

    def validate_and_get_resources(self, data) -> Tuple[User, Topic, Set[str], str]:
        """
        Common validation and resource retrieval logic.

        Args:
            data: Request data to validate (either query_params or request.data)

        Returns:
            Tuple containing user, topic, and question set IDs

        Raises:
            Exception: If serializer_class is not set or validation fails
        """

        self.serializer = self.serializer_class(data=data)
        if not self.serializer.is_valid():
            raise ValidationError(self.serializer.errors)

        user = self.get_user_from_validated_data(self.serializer)
        topic = self.get_topic_from_validated_data(self.serializer)
        user_question_set_instance = self.get_user_question_set(user, topic)
        collection_name = self._get_collection_name_from_topic(topic)

        return (
            user,
            topic,
            user_question_set_instance.get_question_set_ids,
            collection_name,
        )

    @staticmethod
    def validate_question_exists(
        question_id: str, question_set: set[str], username: str
    ) -> bool:
        """Validate if question exists in user's question set."""
        if question_id not in question_set:
            error_msg = f"Question ID '{question_id}' not found in question set for user '{username}'"
            log.error(error_msg)
            raise QuestionNotFoundError(question_id, username)
        return True

    # TODO : add custom error to catch mongo db question not found
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


class GetQuestionsView(QuestionManagementBase):
    """Get questions for a specific user and topic."""

    serializer_class = QueryParamsSerializer

    def get(self, request, username, block_id):
        user, topic, question_set_ids, collection_name = (
            self.validate_and_get_resources(
                data=({"username": username, "block_id": block_id}),
            )
        )

        object_ids = [ObjectId(id) for id in question_set_ids if ObjectId.is_valid(id)]

        if not object_ids:
            log.info(f"No valid question IDs found for user '{username}'")
            return Response(
                {"message": f"No valid question IDs found for user {username}"},
                status=status.HTTP_404_NOT_FOUND,
            )

        docs = self.no_sql_database_client.fetch_from_db(
            collection_name, NO_SQL_DATABASE_NAME, {"_id": {"$in": object_ids}}
        )

        questions = [
            Question(**{**doc, "_id": str(doc["_id"])}).model_dump(
                by_alias=True, exclude={"choices": {"is_correct"}}
            )
            for doc in docs
        ]

        return Response(
            {
                "username": self.serializer.validated_data["username"],
                "block_id": self.serializer.validated_data["block_id"],
                "questions": questions,
            }
        )


class PostQuestionAttemptView(QuestionManagementBase):
    """Handle posting and processing of question attempts."""

    serializer_class = PostQuestionAttemptSerializer
    MAX_ATTEMPTS = config("MAX_QUESTION_ATTEMPTS", default=3, cast=int)

    def __init__(self, database_client: NoSqLDatabaseEngineInterface):
        super().__init__(database_client=database_client)

    def _handle_existing_attempt(self, metadata: Dict[str, Any]) -> Optional[Response]:
        """Handle logic for an existing question attempt."""
        if metadata["is_correct"]:
            return Response(
                {"message": "Question already correctly answered"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if metadata["attempt_number"] >= self.MAX_ATTEMPTS:
            return Response(
                {"message": f"Maximum attempts ({self.MAX_ATTEMPTS}) reached"},
                status=status.HTTP_403_FORBIDDEN,
            )

        return None

    def _is_choice_answer_correct(
        self, choice_id: int, question_id: str, collection_name: str
    ) -> bool:
        result = self.database_client.fetch_from_db(
            collection_name, NO_SQL_DATABASE_NAME, {"_id": ObjectId(question_id)}
        )

        question_instance = Question(**{**result, "_id": str(question_id)})
        if not question_instance.choices[choice_id].is_correct:
            return False
        return True

    @staticmethod
    def _update_question_metadata(
        metadata: Dict[str, Any], is_correct: bool, attempt_number: int
    ) -> Dict[str, Any]:
        """Update the metadata for a question attempt."""
        return {**metadata, "is_correct": is_correct, "attempt_number": attempt_number}

    @QuestionManagementBase.handle_response
    def post(self, request):
        user, topic, question_set_ids, collection_name = (
            self.validate_and_get_resources(request.data)
        )

        question_id = self.serializer.validated_data["question_id"]
        self.validate_question_exists(
            question_id, question_set_ids, self.serializer.validated_data["username"]
        )

        user_question_attempt = get_object_or_404(
            UserQuestionAttempts, user=user, topic=topic
        )
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

        question_metadata[question_id]["choice_id"] = self.serializer.validated_data[
            "choice_id"
        ]
        user_question_attempt.save()

        return Response(
            QuestionAttemptData(
                **question_metadata[question_id],
                total_incorrect_count=user_question_attempt.get_incorrect_questions_count,
                total_correct_count=user_question_attempt.get_correct_questions_count,
            ).model_dump(),
            status=status.HTTP_201_CREATED,
        )


class GetQuestionAttemptView(QuestionManagementBase):
    """Retrieve a question attempt for a user."""

    serializer_class = GetQuestionSerializer

    def __init__(self, database_client: NoSqLDatabaseEngineInterface):
        super().__init__(database_client=database_client)

    @QuestionManagementBase.handle_response
    def get(self, request, username, block_id, question_id):
        user, topic, question_set_ids, _ = self.validate_and_get_resources(
            data=(
                {"username": username, "block_id": block_id, "question_id": question_id}
            ),
        )

        question_id = self.serializer.validated_data["question_id"]
        self.validate_question_exists(
            question_id, question_set_ids, self.serializer.validated_data["username"]
        )

        user_question_attempt = get_object_or_404(
            UserQuestionAttempts, user=user, topic=topic
        )
        response = user_question_attempt.get_latest_question_metadata.get(question_id)
        if not response:
            # means that the question does not yet have an entry in the question attempt metadata
            return Response(
                {
                    "total_correct_count": user_question_attempt.get_correct_questions_count,
                    "total_incorrect_count": user_question_attempt.get_incorrect_questions_count,
                }
            )

        return Response(
            QuestionAttemptData(
                **response,
                total_correct_count=user_question_attempt.get_correct_questions_count,
                total_incorrect_count=user_question_attempt.get_incorrect_questions_count,
            ).model_dump()
        )


def get_database_client() -> MongoDatabaseEngine:
    """
    Factory function to create and configure a MongoDB database client.

    Returns:
        MongoDatabaseEngine: A configured instance of the MongoDB database engine
        with connection settings from common configuration.
    """
    return MongoDatabaseEngine(getattr(common, "MONGO_URL", None))


def get_questions_view_factory(*args, **kwargs):
    """
    Factory function to create a properly configured GetQuestionsView instance.

    Returns:
        Callable: A Django view callable configured with the necessary database client.
    """
    database_client = get_database_client()
    view_instance = GetQuestionsView.as_view(no_sql_database_client=database_client)
    return view_instance


def post_question_attempt_view_factory() -> PostQuestionAttemptView:
    """
    Factory function to create a PostQuestionAttemptView with configured database client.

    This factory handles the creation and injection of the database client
    dependency for the PostQuestionAttemptView.

    Returns:
        Type[PostQuestionAttemptView]: A configured PostQuestionAttemptView class with
        database client dependency injected.
    """
    return PostQuestionAttemptView(database_client=get_database_client())


def get_question_attempt_view_factory() -> GetQuestionAttemptView:
    """
    Factory function to create a GetQuestionAttemptView with configured database client.

    Creates and configures a GetQuestionAttemptView with the appropriate database
    client dependency already injected.

    Returns:
        Type[GetQuestionAttemptView]: A configured GetQuestionAttemptView class with
        database client dependency injected.
    """
    return GetQuestionAttemptView(database_client=get_database_client())
