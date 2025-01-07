from unittest.mock import Mock

import factory
import pytest
from bson import ObjectId
from rest_framework.test import APIClient

from course_ware.serializers import QueryParamsSerializer
from course_ware.tests.course_ware_factory import (
    QuestionMetadataFactory,
    TopicFactory,
    UserFactory,
    UserQuestionAttemptsFactory,
    UserQuestionSetFactory,
)
from course_ware.views import DatabaseQuestionViewBase
from nosql_database_engine import MongoDatabaseEngine


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def mock_db_client():

    mock_client = Mock(spec=MongoDatabaseEngine)
    mock_client.disconnect.side_effect = lambda: None

    return mock_client


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def topic():
    return TopicFactory()


@pytest.fixture
def user_question_attempts(user, topic):
    def generate_question_metadata():
        """
        Generate a dictionary where keys and values' 'id' fields match.
        """

        def create_question():
            question = QuestionMetadataFactory(is_correct=False, attempt_number=2)
            question_id = question.question_id
            return question_id, vars(question)

        return {
            "v1.0.0": dict(create_question() for _ in range(2)),
            "v2.0.0": dict(create_question() for _ in range(1)),
        }

    question_metadata = factory.LazyFunction(generate_question_metadata)

    return UserQuestionAttemptsFactory(
        user=user, topic=topic, question_metadata=question_metadata
    )


@pytest.fixture
def user_question_set(user, topic):
    return UserQuestionSetFactory(
        user=user,
        topic=topic,
        question_list_ids=[
            {"id": "65989c1b4f37a89def123456"},
            {"id": "65989c1b4f37a89def789abc"},
            {"id": "65989c1b4f37a89def456789"},
        ],
    )


@pytest.fixture
def question_management_base(mock_db_client):
    class TestQuestionManagementBase(DatabaseQuestionViewBase):
        serializer_class = QueryParamsSerializer

    return TestQuestionManagementBase(
        no_sql_database_client=mock_db_client,
    )


@pytest.fixture
def url_params(user, user_question_attempts, topic):
    """Fixture for common URL parameters"""
    return {
        "username": user.username,
        "block_id": user_question_attempts.topic.block_id,
        "question_id": str(ObjectId()),
    }
