from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse

from course_ware.views import QuestionManagementBase
from edu_vault.settings import common
from exceptions import ParsingError, QuestionNotFoundError


def test_no_sql_database_client_validation():
    with pytest.raises(ValueError, match="database_client is required"):
        QuestionManagementBase()

    with pytest.raises(ValueError, match="Please use a valid database engine instance"):
        QuestionManagementBase(no_sql_database_client=MagicMock())  # Invalid client


def test_serializer_class_validation(mock_db_client):
    class TestQuestionManagementBase(QuestionManagementBase):
        pass

    with pytest.raises(Exception, match="serializer_class must be set on the view"):
        TestQuestionManagementBase(no_sql_database_client=mock_db_client)


def test_get_collection_name_from_topic(topic):
    with patch.dict(
        common.COURSE_DATABASE_NAME_MAPPING,
        {topic.category.course.course_key: "test_collection"},
    ):
        collection_name = QuestionManagementBase._get_collection_name_from_topic(topic)
        assert collection_name == "test_collection"

    with patch.dict(common.COURSE_DATABASE_NAME_MAPPING, {}):
        with pytest.raises(ParsingError, match="could not find database collection"):
            QuestionManagementBase._get_collection_name_from_topic(topic)


def test_validate_and_get_resources(
    question_management_base, user, topic, user_question_set
):
    serializer_mock = MagicMock()
    serializer_mock.is_valid.return_value = True
    serializer_mock.data = {}

    with patch.object(
        question_management_base,
        "serializer_class",
        return_value=serializer_mock,
    ):
        with patch.object(
            question_management_base,
            "get_user_from_validated_data",
            return_value=user,
        ):
            with patch.object(
                question_management_base,
                "get_topic_from_validated_data",
                return_value=topic,
            ):
                with patch.object(
                    question_management_base,
                    "get_user_question_set",
                    return_value=user_question_set,
                ):
                    with patch.dict(
                        common.COURSE_DATABASE_NAME_MAPPING,
                        {topic.category.course.course_key: "test_collection"},
                    ):
                        result = question_management_base.validate_and_get_resources({})
                        assert len(result) == 4


def test_validate_question_exists():
    with pytest.raises(QuestionNotFoundError, match="Question ID '123' not found"):
        QuestionManagementBase.validate_question_exists("123", {"456"}, "test_user")


def test_get_questions_view(api_client, user, mock_db_client, topic, user_question_set):
    """Tests GetQuestionsView scenarios including edge cases"""
    base_question = {
        "_id": "id",
        "question_id": "id",
        "text": "Test genetics question",
        "topic": "Biology",
        "category": "Genetics",
        "academic_class": "12th Grade",
        "examination_level": "Intermediate",
        "difficulty": "easy",
        "tags": ["biology", "genetics"],
        "choices": [
            {"text": "Option 1", "is_correct": True},
            {"text": "Option 2", "is_correct": False},
        ],
        "solution": {"explanation": "Test explanation", "steps": ["Step 1", "Step 2"]},
        "hint": "Test hint",
        "metadata": {
            "created_by": "teacher",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "time_estimate": 10,
        },
    }

    test_cases = [
        # Success cases
        {
            "name": "valid_single_question",
            "question_ids": ["65989c1b4f37a89def123456"],
            "mock_questions": [
                {
                    **base_question,
                    "_id": "65989c1b4f37a89def123456",
                    "question_id": "65989c1b4f37a89def123456",
                }
            ],
            "expected_status": 200,
            "expected_questions": 1,
            "mock_called": True,
        },
        {
            "name": "valid_multiple_questions",
            "question_ids": ["65989c1b4f37a89def789abc", "65989c1b4f37a89def456789"],
            "mock_questions": [
                {
                    **base_question,
                    "_id": "65989c1b4f37a89def789abc",
                    "question_id": "65989c1b4f37a89def789abc",
                },
                {
                    **base_question,
                    "_id": "65989c1b4f37a89def456789",
                    "question_id": "65989c1b4f37a89def456789",
                },
            ],
            "expected_status": 200,
            "expected_questions": 2,
            "mock_called": True,
        },
        # Failure cases
        {
            "name": "empty_question_set",
            "question_ids": [],
            "mock_questions": [],
            "expected_status": 404,
            "expected_message": f"No valid question IDs found for user {user.username}",
            "mock_called": False,
        },
        {
            "name": "invalid_object_ids",
            "question_ids": ["invalid-id-1", "invalid-id-2"],
            "mock_questions": [],
            "expected_status": 404,
            "expected_message": f"No valid question IDs found for user {user.username}",
            "mock_called": False,
        },
        # Edge cases
        {
            "name": "mixed_valid_invalid_ids",
            "question_ids": ["65989c1b4f37a89def123456", "invalid-id"],
            "mock_questions": [
                {
                    **base_question,
                    "_id": "65989c1b4f37a89def123456",
                    "question_id": "65989c1b4f37a89def123456",
                }
            ],
            "expected_status": 200,
            "expected_questions": 1,
            "mock_called": True,
        },
        {
            "name": "duplicate_question_ids",
            "question_ids": ["65989c1b4f37a89def123456", "65989c1b4f37a89def123456"],
            "mock_questions": [
                {
                    **base_question,
                    "_id": "65989c1b4f37a89def123456",
                    "question_id": "65989c1b4f37a89def123456",
                }
            ],
            "expected_status": 200,
            "expected_questions": 1,
            "mock_called": True,
        },
        {
            "name": "malformed_object_id",
            "question_ids": ["!@#$%^&*()"],
            "mock_questions": [],
            "expected_status": 404,
            "expected_message": f"No valid question IDs found for user {user.username}",
            "mock_called": False,
        },
    ]

    course_mapping = {topic.category.course.course_key: "test_collection"}

    for case in test_cases:
        with patch(
            "course_ware.views.get_database_client", return_value=mock_db_client
        ), patch.dict(common.COURSE_DATABASE_NAME_MAPPING, course_mapping):

            user_question_set.question_list_ids = [
                {"id": id} for id in case["question_ids"]
            ]
            user_question_set.save()

            mock_db_client.fetch_from_db.return_value = case["mock_questions"]
            url = reverse(
                "course_ware:problem_view", args=[user.username, topic.block_id]
            )

            response = api_client.get(url)
            assert response.status_code == case["expected_status"]

            if case["expected_status"] == 200:
                assert len(response.data["questions"]) == case["expected_questions"]
                assert all(
                    "is_correct" not in str(q["choices"])
                    for q in response.data["questions"]
                )
                if case["question_ids"]:
                    assert (
                        response.data["questions"][0]["_id"]
                        in user_question_set.get_question_set_ids
                    )
            else:
                assert case["expected_message"] == response.data["message"]

            if case["mock_called"]:
                mock_db_client.fetch_from_db.assert_called_once()
            else:
                mock_db_client.fetch_from_db.assert_not_called()

            mock_db_client.reset_mock()
            user_question_set.question_list_ids = []
            user_question_set.save()
