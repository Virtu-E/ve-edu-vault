import logging

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


class PostQuestionAttemptView(RetrieveUserAndResourcesMixin, APIView):
    """
    Post question attempts for a specific user and topic.
    """

    def post(self, request):
        serializer = QuestionAttemptSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # we have the user question attempt data. now we have to get the question attempt model
        user = self.get_user_from_validated_data(serializer)
        topic = self.get_topic_from_validated_data(serializer)
        question_set = self.get_user_question_set(user, topic).get_question_set_ids

        user_question_attempt = get_object_or_404(
            UserQuestionAttempts, user=user, topic=topic
        )
        question_metadata = user_question_attempt.get_latest_question_metadata
        # now we have to update the question data inside the question metadata
        question_metadata_instance = question_metadata.get(
            serializer.validated_data["question_id"], None
        )

        if question_metadata_instance:
            # we only want to update if the user has not gotten the question correctly
            if question_metadata_instance["is_correct"]:
                return

            # user has maxed out all the chances needed to get the question correct. Hence, officially  failed
            if question_metadata_instance["attempt_number"] == 3:
                return

            question_metadata_instance["attempt_number"] = (
                question_metadata_instance["attempt_number"] + 1
            )
            user_question_attempt.save()
            return Response(
                "Question Attempt data Saved", status=status.HTTP_201_CREATED
            )

        # the question metadata for the question ID as not yet been created
        # but we need to validate if the question ID exists in the user question set
        if not serializer.validated_data["question_id"] in question_set:
            # the supplied question ID does not correlate with the questions ID in the user question set
            log.error(
                "The supplied question ID '%s' does not match any question ID in the UserQuestionSet for the user '%s'.",
                serializer.validated_data["question_id"],
                serializer.validated_data["username"],
            )

            return Response(
                {
                    "error": (
                        "The supplied question ID '%s' does not match any question ID in the UserQuestionSet for the user '%s'.",
                        serializer.validated_data["question_id"],
                        serializer.validated_data["username"],
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # create the question metadata and then return a success
