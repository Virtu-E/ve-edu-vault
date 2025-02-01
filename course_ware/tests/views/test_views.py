from unittest.mock import MagicMock, patch

import pytest
from bson import ObjectId
from django.urls import reverse
from rest_framework import status

from course_ware.serializers import QueryParamsSerializer
from course_ware.tests.course_ware_factory import QuestionFactory
from course_ware.views import DatabaseQuestionViewBase, PostQuestionAttemptView
from edu_vault.settings import common
from exceptions import ParsingError, QuestionNotFoundError


class TestDatabaseQuestionViewBase:
    """
    Tests the DatabaseQuestionViewBase Django View class
    """

    def test_no_sql_database_client_validation(self):
        class TestQuestionManagementBase(DatabaseQuestionViewBase):
            serializer_class = QueryParamsSerializer

        with pytest.raises(ValueError, match="database_client is required"):
            TestQuestionManagementBase()

        with pytest.raises(ValueError, match="Please use a valid database engine instance"):
            TestQuestionManagementBase(no_sql_database_client=MagicMock())  # Invalid client

    def test_serializer_class_validation(self, mock_db_client):
        class TestQuestionManagementBase(DatabaseQuestionViewBase):
            pass

        with pytest.raises(Exception, match="serializer_class must be set on the view"):
            TestQuestionManagementBase(no_sql_database_client=mock_db_client)

    def test_get_collection_name_from_topic(self, topic):
        with patch.dict(
            common.COURSE_DATABASE_NAME_MAPPING,
            {topic.category.course.course_key: "test_collection"},
        ):
            collection_name = DatabaseQuestionViewBase._get_collection_name_from_topic(topic)
            assert collection_name == "test_collection"

        with patch.dict(common.COURSE_DATABASE_NAME_MAPPING, {}):
            with pytest.raises(ParsingError, match="could not find database collection"):
                DatabaseQuestionViewBase._get_collection_name_from_topic(topic)

    def test_validate_and_get_resources(self, question_management_base, user, topic, user_question_set):
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

    def test_validate_question_exists(self):
        with pytest.raises(QuestionNotFoundError, match="Question ID '123' not found"):
            DatabaseQuestionViewBase.validate_question_exists("123", {"456"}, "test_user")


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
        with (
            patch(
                "course_ware.factory_views.MongoDatabaseEngine",
                return_value=mock_db_client,
            ),
            patch.dict(common.COURSE_DATABASE_NAME_MAPPING, course_mapping),
        ):
            user_question_set.question_list_ids = [{"id": id} for id in case["question_ids"]]
            user_question_set.save()

            mock_db_client.fetch_from_db.return_value = case["mock_questions"]
            url = reverse("course_ware:get_questions_view", args=[user.username, topic.block_id])

            response = api_client.get(url)
            assert response.status_code == case["expected_status"]

            if case["expected_status"] == 200:
                assert len(response.data["questions"]) == case["expected_questions"]
                assert all("is_correct" not in str(q["choices"]) for q in response.data["questions"])
                if case["question_ids"]:
                    assert response.data["questions"][0]["_id"] in user_question_set.get_question_set_ids
            else:
                assert case["expected_message"] == response.data["message"]

            if case["mock_called"]:
                mock_db_client.fetch_from_db.assert_called_once()
            else:
                mock_db_client.fetch_from_db.assert_not_called()

            mock_db_client.reset_mock()
            user_question_set.question_list_ids = []
            user_question_set.save()


class TestPostQuestionAttemptView:
    """
    Test cases for PostQuestionAttemptView Django View Class
    """

    @pytest.mark.parametrize(
        "metadata,expected_status,expected_message",
        [
            (
                {"is_correct": True, "attempt_number": 1},
                status.HTTP_400_BAD_REQUEST,
                "Question already correctly answered",
            ),
            (
                {"is_correct": True, "attempt_number": 3},
                status.HTTP_400_BAD_REQUEST,
                "Question already correctly answered",
            ),
        ],
    )
    def test_handle_existing_attempt_correct_answer(self, mock_db_client, metadata, expected_status, expected_message):
        """Test handling of attempts for already correctly answered questions"""
        view = PostQuestionAttemptView(no_sql_database_client=mock_db_client)
        response = view._handle_existing_attempt(metadata)
        assert response.status_code == expected_status
        assert response.data["message"] == expected_message

    @pytest.mark.parametrize(
        "attempt_number,max_attempts",
        [
            (3, 3),
            (4, 3),
            (5, 3),
        ],
    )
    def test_handle_existing_attempt_max_attempts(self, mock_db_client, attempt_number, max_attempts):
        """Test handling of attempts when max attempts are reached"""
        metadata = {"is_correct": False, "attempt_number": attempt_number}
        view = PostQuestionAttemptView(no_sql_database_client=mock_db_client)
        response = view._handle_existing_attempt(metadata)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["message"] == f"Maximum attempts ({max_attempts}) reached"

    @pytest.mark.parametrize(
        "metadata,is_correct,attempt_number,expected",
        [
            (
                {"is_correct": False, "attempt_number": 1, "extra": "data"},
                True,
                2,
                {"is_correct": True, "attempt_number": 2, "extra": "data"},
            ),
            (
                {"is_correct": True, "attempt_number": 2},
                False,
                3,
                {"is_correct": False, "attempt_number": 3},
            ),
        ],
    )
    def test_update_question_metadata(self, metadata, is_correct, attempt_number, expected):
        """Test question metadata updates preserve existing fields"""
        updated_metadata = PostQuestionAttemptView._update_question_metadata(metadata, is_correct=is_correct, attempt_number=attempt_number)
        assert updated_metadata == expected

    def test_is_choice_answer_correct(self, mock_db_client):
        """Test correct answer validation"""
        # Setup mock response
        question_id = str(ObjectId())

        mock_db_client.fetch_from_db.return_value = [
            QuestionFactory(
                choices=[
                    {"is_correct": True, "text": "Hello World"},
                    {"is_correct": False, "text": "Hello Japan"},
                    {"is_correct": False, "text": "Hello Malawi"},
                ]
            ).__dict__
        ]

        view = PostQuestionAttemptView(no_sql_database_client=mock_db_client)

        # Test correct choice
        assert view._is_choice_answer_correct(0, question_id, "test_collection") is True

        # Test incorrect choice
        assert view._is_choice_answer_correct(1, question_id, "test_collection") is False

    def test_post_first_attempt_incorrect(
        self,
        api_client,
        user,
        mock_db_client,
        user_question_attempts,
        topic,
        user_question_set,
    ):
        """Test first attempt with incorrect answer"""
        question_id = next(iter(user_question_attempts.get_latest_question_metadata))
        request_data = {
            "question_id": question_id,
            "choice_id": 1,
            "difficulty": "easy",
            "username": user.username,
            "block_id": user_question_attempts.topic.block_id,
        }

        user_question_set.question_list_ids = [{"id": question_id}]
        user_question_set.save()

        url = reverse("course_ware:post_question_attempt_view")

        with (
            patch(
                "course_ware.views.PostQuestionAttemptView._is_choice_answer_correct",
                return_value=False,
            ),
            patch.dict(
                common.COURSE_DATABASE_NAME_MAPPING,
                {user_question_attempts.topic.category.course.course_key: "test_collection"},
            ),
        ):
            response = api_client.post(url, data=request_data)

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data["is_correct"] is False
        assert response_data["attempt_number"] == 3

    def test_post_invalid_question_id(
        self,
        api_client,
        user,
        mock_db_client,
        user_question_attempts,
        topic,
        user_question_set,
    ):
        """Test attempt with an invalid question ID."""
        # Arrange
        request_data = {
            "question_id": "invalid_id",
            "choice_id": 0,
            "difficulty": "easy",
            "username": user.username,
            "block_id": user_question_attempts.topic.block_id,
        }

        url = reverse("course_ware:post_question_attempt_view")

        # Mock dependencies
        with patch.dict(
            common.COURSE_DATABASE_NAME_MAPPING,
            {user_question_attempts.topic.category.course.course_key: "test_collection"},
        ):
            # Act & Assert
            with pytest.raises(QuestionNotFoundError):
                api_client.post(url, data=request_data)

    def test_post_nonexistent_user(self, api_client, mock_db_client, user_question_attempts, topic):
        """Test attempt with non-existent user"""
        request_data = {
            "question_id": str(ObjectId()),
            "choice_id": 0,
            "difficulty": "easy",
            "username": "nonexistent_user",
            "block_id": user_question_attempts.topic.block_id,
        }

        url = reverse("course_ware:post_question_attempt_view")
        response = api_client.post(url, data=request_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        "missing_field",
        ["question_id", "choice_id", "difficulty", "username", "block_id"],
    )
    def test_post_missing_required_fields(
        self,
        api_client,
        user,
        mock_db_client,
        user_question_attempts,
        topic,
        missing_field,
    ):
        """Test attempts with missing required fields"""
        request_data = {
            "question_id": str(ObjectId()),
            "choice_id": 0,
            "difficulty": "easy",
            "username": user.username,
            "block_id": user_question_attempts.topic.block_id,
        }
        del request_data[missing_field]

        url = reverse("course_ware:post_question_attempt_view")
        response = api_client.post(url, data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.skip("broken test, needs fixing")
    def test_post_invalid_choice_id(
        self,
        api_client,
        user,
        mock_db_client,
        user_question_attempts,
        topic,
        user_question_set,
    ):
        """Test attempt with invalid choice ID"""
        question_id = next(iter(user_question_attempts.get_latest_question_metadata))
        request_data = {
            "question_id": question_id,
            "choice_id": 999,  # Invalid choice ID
            "difficulty": "easy",
            "username": user.username,
            "block_id": user_question_attempts.topic.block_id,
        }

        user_question_set.question_list_ids = [{"id": question_id}]
        user_question_set.save()

        url = reverse("course_ware:post_question_attempt_view")

        with patch.dict(
            common.COURSE_DATABASE_NAME_MAPPING,
            {user_question_attempts.topic.category.course.course_key: "test_collection"},
        ):
            response = api_client.post(url, data=request_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestGetQuestionAttemptView:
    """
    Test cases for GetQuestionAttemptView
    """

    def test_get_existing_question_attempt(
        self,
        api_client,
        user,
        user_question_attempts,
        topic,
        user_question_set,
        url_params,
    ):
        """
        Test retrieving an existing question attempt with metadata
        """
        # Arrange
        question_id = url_params["question_id"]

        # Setup question metadata
        attempt_data = {
            "is_correct": True,
            "attempt_number": 2,
            "difficulty": "medium",
            "topic": topic.name,
            "question_id": question_id,
            "choice_id": 1,
        }

        user_question_attempts.get_latest_question_metadata[question_id] = attempt_data
        user_question_attempts.save()

        # Setup question set
        user_question_set.question_list_ids = [{"id": question_id}]
        user_question_set.save()

        url = reverse("course_ware:get_question_attempt_view", kwargs=url_params)

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data["is_correct"] == attempt_data["is_correct"]
        assert response_data["attempt_number"] == attempt_data["attempt_number"]
        assert response_data["difficulty"] == attempt_data["difficulty"]
        assert response_data["topic"] == attempt_data["topic"]
        assert response_data["question_id"] == attempt_data["question_id"]
        assert response_data["choice_id"] == attempt_data["choice_id"]
        assert "total_correct_count" in response_data
        assert "total_incorrect_count" in response_data

    def test_get_non_existing_question_attempt(self, api_client, user, user_question_attempts, user_question_set, url_params):
        """
        Test retrieving a question attempt data that doesn't exist
        """
        # Arrange
        question_id = url_params["question_id"]

        # Setup question set
        user_question_set.question_list_ids = [{"id": question_id}]
        user_question_set.save()

        url = reverse("course_ware:get_question_attempt_view", kwargs=url_params)

        # Act
        response = api_client.get(url)

        # Assert
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert len(response_data) == 2
        assert "total_correct_count" in response_data
        assert "total_incorrect_count" in response_data

    def test_get_attempt_nonexistent_user(self, api_client, user_question_attempts, topic):
        """
        Test retrieving attempt for non-existent user
        """
        params = {
            "username": "nonexistent_user",
            "block_id": user_question_attempts.topic.block_id,
            "question_id": str(ObjectId()),
        }

        url = reverse("course_ware:get_question_attempt_view", kwargs=params)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_attempt_invalid_block_id(self, api_client, user):
        """
        Test retrieving attempt with invalid block ID
        """
        params = {
            "username": user.username,
            "block_id": "invalid_block_id",
            "question_id": str(ObjectId()),
        }

        url = reverse("course_ware:get_question_attempt_view", kwargs=params)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_attempt_invalid_question_id(self, api_client, user, user_question_attempts, user_question_set, topic):
        """
        Test retrieving attempt with invalid question ID
        """
        params = {
            "username": user.username,
            "block_id": user_question_attempts.topic.block_id,
            "question_id": "invalid_question_id",
        }

        url = reverse("course_ware:get_question_attempt_view", kwargs=params)
        with pytest.raises(QuestionNotFoundError):
            api_client.get(url)

    def test_get_attempt_question_not_in_set(self, api_client, user, user_question_attempts, user_question_set, url_params):
        """
        Test retrieving attempt for question not in question set
        """
        # Question ID not added to question_set.question_list_ids
        url = reverse("course_ware:get_question_attempt_view", kwargs=url_params)
        # TODO : i think it should return a 400 error to the browser as well. Instead of just raising a 500 error
        with pytest.raises(QuestionNotFoundError):
            api_client.get(url)
