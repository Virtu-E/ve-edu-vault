import logging
from typing import Any, Dict, Optional

from bson import ObjectId  # For MongoDB ObjectId handling
from django.shortcuts import get_object_or_404
from pydantic_core import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from course_ware.mixins import RetrieveUserAndResourcesMixin
from course_ware.models import UserQuestionAttempts
from course_ware.serializers import QueryParamsSerializer, QuestionAttemptSerializer
from data_types.questions import Question
from edu_vault.settings import common
from exceptions import TypeValidationError
from nosql_database_engine import MongoDatabaseEngine

log = logging.getLogger(__name__)


class DatabaseView(APIView):
    def __init__(self):
        super(DatabaseView, self).__init__()
        self.mongo_client = MongoDatabaseEngine(getattr(common, "MONGO_URL", None))


class GetQuestionsView(RetrieveUserAndResourcesMixin, DatabaseView):
    """
    Get questions for a specific user and topic.
    """

    def get(self, request):
        serializer = QueryParamsSerializer(data=request.query_params)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = self.get_user_from_validated_data(serializer)
            topic = self.get_topic_from_validated_data(serializer)
            question_set = self.get_user_question_set(user, topic)

            # Extract question IDs from the question set
            question_ids = question_set.get_question_set_ids

            mongo_client = self.mongo_client.fetch_from_db(
                "mathematics_problems", "virtu_educate"
            )

            # Fetch questions from MongoDB by their IDs
            try:
                questions = [
                    Question(**doc).model_dump()
                    for doc in mongo_client.find(
                        {"_id": {"$in": [ObjectId(id) for id in question_ids]}}
                    )
                ]

            # TODO : make this dynamic
            except ValidationError as e:
                log.error(
                    f"Validation failed for database virtu_educate and collection mathematics_problems, error: {e}"
                )
                raise TypeValidationError(
                    f"Validation failed for database virtu_educate and collection mathematics_problems, error: {e}"
                )

            return Response(
                {
                    "username": serializer.validated_data["username"],
                    "topic": serializer.validated_data["topic_id"],
                    "questions": questions,
                    "question_attempts": "",
                }
            )

        except Exception as e:
            log.error(
                f'failed to get questions for user "{serializer.validated_data["username"]} : {e}"'
            )
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# TODO : how to handle really long post code blocks. Look at edx and anthropic codebase
class PostQuestionAttemptView(RetrieveUserAndResourcesMixin, APIView):
    """
    API View to handle posting and processing of question attempts for a specific user and topic.

    This view manages:
    - Validation of question attempts
    - Tracking attempt counts
    - Managing question metadata
    - Enforcing attempt limits

    Attributes:
        MAX_ATTEMPTS (int): Maximum number of attempts allowed per question
    """

    MAX_ATTEMPTS = 3

    @staticmethod
    def _validate_question_exists(
        question_id: str, question_set: set[str], username: str
    ) -> bool:
        """
        Validate if the given question ID exists in the user's question set.

        Args:
            question_id: The ID of the question being attempted
            question_set: Set of valid question IDs for the user
            username: Username for logging purposes

        Returns:
            bool: True if question exists

        Raises:
            ValidationError: If question ID does not exist
        """
        if question_id not in question_set:
            error_msg = f"Question ID '{question_id}' not found in question set for user '{username}'"
            log.error(error_msg)
            raise ValidationError(error_msg)
        return True

    def _handle_existing_attempt(self, metadata: Dict[str, Any]) -> Optional[Response]:
        """
        Handle logic for an existing question attempt.

        Args:
            metadata: Current question metadata

        Returns:
            Response if attempt should be rejected, None if attempt is valid
        """
        if metadata["is_correct"]:
            return Response(
                {"message": "Question already correctly answered"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if metadata["attempt_number"] >= self.MAX_ATTEMPTS:
            return Response(
                {"message": f"Maximum attempts ({self.MAX_ATTEMPTS}) reached"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return None

    # TODO : update it with the necessary topics etc
    @staticmethod
    def _update_question_metadata(
        metadata: Dict[str, Any], is_correct: bool, attempt_number: int
    ) -> Dict[str, Any]:
        """
        Update the metadata for a question attempt.

        Args:
            metadata: Current question metadata
            is_correct: Whether the attempt was correct
            attempt_number: Current attempt number

        Returns:
            Dict containing updated metadata of type QuestionMetadata
        """
        return {**metadata, "is_correct": is_correct, "attempt_number": attempt_number}

    def post(self, request):
        try:
            serializer = QuestionAttemptSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # we have the user question attempt data. now we have to get the question attempt model
            user = self.get_user_from_validated_data(serializer)
            topic = self.get_topic_from_validated_data(serializer)
            user_question_set = self.get_user_question_set(
                user, topic
            ).get_question_set_ids
            question_id = serializer.validated_data["question_id"]

            self._validate_question_exists(
                question_id, user_question_set, serializer.validated_data["username"]
            )

            user_question_attempt = get_object_or_404(
                UserQuestionAttempts, user=user, topic=topic
            )
            question_metadata = user_question_attempt.get_latest_question_metadata

            question_metadata_instance = question_metadata.get(
                serializer.validated_data["question_id"], None
            )

            if question_metadata_instance:
                # Handle existing attempt
                response = self._handle_existing_attempt(question_metadata_instance)
                if response:
                    return response

                # Update attempt count
                question_metadata[question_id] = self._update_question_metadata(
                    question_metadata_instance,
                    is_correct=question_metadata_instance["is_correct"],
                    attempt_number=question_metadata_instance["attempt_number"] + 1,
                )
            else:

                # Create new metadata entry
                question_metadata[question_id] = {
                    "is_correct": serializer.validated_data["username"],
                    "attempt_number": 1,
                    "difficulty": serializer.validated_data["difficulty"],
                    "topic": topic.name,
                    "question_id": question_id,
                }

            user_question_attempt.save()

            return Response(
                {"message": "Question attempt recorded successfully"},
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            log.error(str(e))
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
