import logging

from bson import ObjectId  # For MongoDB ObjectId handling
from django.shortcuts import get_object_or_404
from pydantic_core import ValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from course_ware.models import Topic, User, UserQuestionSet
from course_ware.serializers import QueryParamsSerializer
from data_types.questions import Question
from edu_vault.settings import common
from exceptions import TypeValidationError
from nosql_database_engine import MongoDatabaseEngine

log = logging.getLogger(__name__)


class DatabaseView(APIView):
    def __init__(self):
        super(DatabaseView, self).__init__()
        self.mongo_client = MongoDatabaseEngine(getattr(common, "MONGO_URL", None))


class GetQuestionsView(DatabaseView):
    """
    Get questions for a specific user and topic.
    """

    def get(self, request):
        serializer = QueryParamsSerializer(data=request.query_params)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get user and topic from the database
            user = get_object_or_404(
                User, username=serializer.validated_data["username"]
            )
            # TODO : i have to provide more data like category, course etc
            # Provide topic ID/block ID here
            topic = get_object_or_404(
                Topic, block_id=serializer.validated_data["topic_id"]
            )

            # Get the associated UserQuestionSet for the user and topic
            question_set = get_object_or_404(UserQuestionSet, user=user, topic=topic)

            # Extract question IDs from the question set
            question_ids = [str(item["id"]) for item in question_set.question_set_ids]

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
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PostQuestionAttemptView(APIView):
    """
    Post question attempts for a specific user and topic.
    """

    def post(self, request):
        pass
