from unittest.mock import patch

import pytest
from django.urls import reverse

from course_ware.serializers import QueryParamsSerializer
from course_ware.views import GetQuestionsView
from edu_vault.settings import common


@pytest.mark.skip("Needs fixing")
def test_validate_and_get_resources(user, topic, mock_db_client, user_question_set):
    """Test resource validation with dependency-injected database client."""
    view = GetQuestionsView(database_client=mock_db_client)
    view.serializer_class = QueryParamsSerializer

    data = {"username": user.username, "block_id": "block1"}

    with patch.object(
        view, "get_user_from_validated_data", return_value=user
    ), patch.object(
        view, "get_topic_from_validated_data", return_value=topic
    ), patch.object(
        view, "get_user_question_set", return_value=user_question_set
    ), patch.object(
        view, "_get_collection_name_from_topic", return_value="sample collection"
    ):
        user_obj, topic_obj, question_set, collection_name = (
            view.validate_and_get_resources(data)
        )

        assert user_obj == user
        assert topic_obj == topic
        # the user does not have any configured question sets, hence an empty set is returned
        assert question_set == set()
        assert collection_name == "sample collection"


def test_get_questions_view_returns_200(
    api_client, user, mock_db_client, topic, user_question_set
):
    """Test GetQuestionsView with mocked database client."""

    # Configure the mock database client response
    mock_db_client.fetch_from_db.return_value = [
        {
            "_id": "question_4",
            "question_id": "question_4",
            "text": "Test question 4",
            "topic": "Biology",
            "category": "Genetics",
            "academic_class": "12th Grade",
            "examination_level": "Intermediate",
            "difficulty": "easy",
            "tags": ["biology", "genetics", "revision"],
            "choices": [
                {"text": "Option 1", "is_correct": True},
                {"text": "Option 2", "is_correct": False},
                {"text": "Option 3", "is_correct": True},
                {"text": "Option 4", "is_correct": False},
            ],
            "solution": {
                "explanation": "Explanation for question 4",
                "steps": [
                    "Step 1: Understand Mendelian ratios",
                    "Step 2: Apply Punnett square",
                ],
            },
            "hint": "Hint for question 4",
            "metadata": {
                "created_by": "teacher",
                "created_at": "2024-12-17T11:00:00",
                "updated_at": "2024-12-19T13:15:00",
                "time_estimate": 8,
            },
        }
    ]
    course_mapping = {topic.category.course.course_key: "no sql database collection"}

    # Patch the database client factory to return the mock client
    with patch(
        "course_ware.views.get_database_client", return_value=mock_db_client
    ), patch.dict(common.COURSE_DATABASE_NAME_MAPPING, course_mapping):
        url = reverse("course_ware:problem_view", args=[user.username, topic.block_id])

        response = api_client.get(url)
        assert response.status_code == 200
        assert "questions" in response.data
        mock_db_client.fetch_from_db.assert_called_once()
