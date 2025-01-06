from unittest.mock import Mock

import pytest
from rest_framework.test import APIClient

from course_ware.tests.course_ware_factory import (
    TopicFactory,
    UserFactory,
    UserQuestionAttemptsFactory,
    UserQuestionSetFactory,
)
from course_ware.views import GetQuestionsView, PostQuestionAttemptView
from nosql_database_engine import MongoDatabaseEngine


@pytest.fixture
def api_client():
    return APIClient()


# @pytest.fixture
# def mock_mongo_client():
#     with patch("nosql_database_engine.MongoDatabaseEngine") as mock:
#         yield mock.return_value


# @pytest.fixture
# def mock_mongo_client():
#     with patch("nosql_database_engine.MongoDatabaseEngine") as mock_engine:
#         mock_instance = MagicMock()
#         mock_engine.return_value = mock_instance
#
#         # Mock methods like fetch_from_db, write_to_db, etc.
#         mock_instance.fetch_from_db.return_value = [
#             {"_id": "fake_id", "question_text": "Mock Question"}
#         ]
#         mock_instance.write_to_db.return_value = None
#         yield mock_instance


@pytest.fixture
def mock_db_client():

    mock_client = Mock(spec=MongoDatabaseEngine)
    mock_client.disconnect.side_effect = lambda: None

    return mock_client


@pytest.fixture
def question_view(mock_db_client):
    """Fixture to create a GetQuestionsView instance with mock database client."""
    return GetQuestionsView(database_client=mock_db_client)


@pytest.fixture
def post_attempt_view(mock_db_client):
    """Fixture to create a PostQuestionAttemptView instance with mock database client."""
    return PostQuestionAttemptView(database_client=mock_db_client)


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def topic():
    return TopicFactory()


@pytest.fixture
def user_question_attempts(user, topic):
    return UserQuestionAttemptsFactory(user=user, topic=topic)


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
