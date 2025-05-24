import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.repository.grading_response_repository.base_response_repository import (
    AbstractGradingResponseRepository,
)
from src.repository.grading_response_repository.response_data_types import (
    Feedback as ResponseFeedback,
)
from src.repository.grading_response_repository.response_data_types import (
    GradedResponse,
)
from src.repository.grading_response_repository.tests.factories import (
    CorrectQuestionAttemptFactory,
    IncorrectQuestionAttemptFactory,
)

from ..data_types import Feedback, GradingResponse
from ..grading_response_service import GradingResponseService
from .factories import (
    FeedbackFactory,
    GradingResponseFactory,
    MultipleChoiceAnswerFactory,
)


@pytest.fixture
def sample_feedback():
    """Fixture to create a sample feedback object using the factory."""
    return FeedbackFactory(
        message="Good job!",
        explanation="Your answer demonstrates understanding of the concept.",
        steps=["Identify the variables", "Apply the formula", "Calculate the result"],
        hint="Remember to check your units",
        show_solution=False,
        misconception=None,
    )


@pytest.fixture
def sample_grading_response(sample_feedback):
    """Fixture to create a sample grading response using the factory."""
    return GradingResponseFactory(
        question_metadata={"difficulty": "medium", "topic": "algebra"},
        success=True,
        is_correct=True,
        score=10.0,
        feedback=sample_feedback,
        attempts_remaining=2,
        question_type="multiple-choice",
    )


@pytest.fixture
def sample_attempted_answer():
    """Fixture to create a sample attempted answer using the factory."""
    return MultipleChoiceAnswerFactory(
        question_metadata={"selected_option": "B", "time_taken": 45}
    )


@pytest.fixture
def mock_repository():
    """Fixture to create a mock repository for testing."""
    repo = AsyncMock(spec=AbstractGradingResponseRepository)
    repo.save_grading_response = AsyncMock(return_value=True)
    repo.get_grading_responses = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def grading_service(mock_repository):
    """Fixture to create a service instance with a mock repository."""
    return GradingResponseService(
        repository=mock_repository, collection_name="test_collection"
    )


@pytest.fixture
def sample_assessment_id():
    """Fixture to create a sample UUID for assessment."""
    return uuid.uuid4()


@pytest.fixture
def sample_question_attempts():
    """Fixture to create sample question attempts."""
    return [
        CorrectQuestionAttemptFactory(
            question_id="q1",
            user_id=12345,
            attempts_remaining=2,
        ),
        IncorrectQuestionAttemptFactory(
            question_id="q2",
            user_id=12345,
            attempts_remaining=1,
        ),
    ]


class TestGradingResponseService:
    """Test suite for the GradingResponseService class."""

    @pytest.mark.asyncio
    async def test_init_sets_repository_and_collection(self, mock_repository):
        """Test that initialization properly sets the repository and collection name."""
        # Arrange
        collection_name = "test_collection"

        # Act
        service = GradingResponseService(
            repository=mock_repository, collection_name=collection_name
        )

        # Assert
        assert service.repository == mock_repository
        assert service.collection_name == collection_name

    @pytest.mark.asyncio
    async def test_save_grading_response_success(
        self,
        grading_service,
        mock_repository,
        sample_grading_response,
        sample_assessment_id,
    ):
        """Test successful saving of a grading response."""
        # Arrange
        user_id = "test_user"
        question_id = "test_question"
        assessment_id = sample_assessment_id
        topic = "Math"
        sub_topic = "Algebra"
        learning_objective = "Solve quadratic equations"
        question_type = "multiple-choice"

        # Act
        result = await grading_service.save_grading_response(
            user_id=user_id,
            question_id=question_id,
            assessment_id=assessment_id,
            grading_response=sample_grading_response,
            topic=topic,
            sub_topic=sub_topic,
            learning_objective=learning_objective,
            question_type=question_type,
        )

        # Assert
        assert result is True
        mock_repository.save_grading_response.assert_awaited_once_with(
            user_id=user_id,
            question_id=question_id,
            assessment_id=assessment_id,
            response=sample_grading_response,
            collection_name=grading_service.collection_name,
        )

    @pytest.mark.asyncio
    async def test_save_grading_response_persists_correct_data(
        self,
        grading_service,
        mock_repository,
        sample_grading_response,
        sample_assessment_id,
    ):
        """Test that the correct data is passed to the repository when saving a response."""
        # Arrange
        user_id = "test_user"
        question_id = "test_question"
        assessment_id = sample_assessment_id

        # Create a custom capture for the arguments
        async def capture_args(**kwargs):
            capture_args.captured = kwargs
            return True

        capture_args.captured = None
        mock_repository.save_grading_response.side_effect = capture_args

        # Act
        await grading_service.save_grading_response(
            user_id=user_id,
            question_id=question_id,
            assessment_id=assessment_id,
            grading_response=sample_grading_response,
        )

        # Assert
        assert capture_args.captured is not None
        assert capture_args.captured["user_id"] == user_id
        assert capture_args.captured["question_id"] == question_id
        assert capture_args.captured["assessment_id"] == assessment_id
        assert capture_args.captured["response"] == sample_grading_response
        assert (
            capture_args.captured["collection_name"] == grading_service.collection_name
        )

        # Verify that the feedback object is correctly passed through
        saved_response = capture_args.captured["response"]
        assert (
            saved_response.feedback.message == sample_grading_response.feedback.message
        )
        assert (
            saved_response.feedback.explanation
            == sample_grading_response.feedback.explanation
        )
        assert saved_response.feedback.steps == sample_grading_response.feedback.steps
        assert saved_response.is_correct == sample_grading_response.is_correct
        assert saved_response.score == sample_grading_response.score

    @pytest.mark.asyncio
    async def test_save_grading_response_failure(
        self,
        grading_service,
        mock_repository,
        sample_grading_response,
        sample_assessment_id,
    ):
        """Test failed saving of a grading response."""
        # Arrange
        user_id = "test_user"
        question_id = "test_question"
        assessment_id = sample_assessment_id

        # Setup the mock to return False (failure)
        mock_repository.save_grading_response.return_value = False

        # Act
        result = await grading_service.save_grading_response(
            user_id=user_id,
            question_id=question_id,
            assessment_id=assessment_id,
            grading_response=sample_grading_response,
        )

        # Assert
        assert result is False
        mock_repository.save_grading_response.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_save_grading_response_with_minimal_params(
        self,
        grading_service,
        mock_repository,
        sample_grading_response,
        sample_assessment_id,
    ):
        """Test saving a grading response with only required parameters."""
        # Arrange
        user_id = "test_user"
        question_id = "test_question"
        assessment_id = sample_assessment_id

        # Act
        result = await grading_service.save_grading_response(
            user_id=user_id,
            question_id=question_id,
            assessment_id=assessment_id,
            grading_response=sample_grading_response,
        )

        # Assert
        assert result is True
        mock_repository.save_grading_response.assert_awaited_once_with(
            user_id=user_id,
            question_id=question_id,
            assessment_id=assessment_id,
            response=sample_grading_response,
            collection_name=grading_service.collection_name,
        )

    @pytest.mark.asyncio
    async def test_get_grading_responses(
        self,
        grading_service,
        mock_repository,
        sample_assessment_id,
        sample_question_attempts,
    ):
        """Test retrieving grading responses."""
        # Arrange
        user_id = "test_user"
        collection_name = "test_collection"
        mock_repository.get_grading_responses.return_value = sample_question_attempts

        # Act
        result = await grading_service.get_grading_responses(
            user_id=user_id,
            assessment_id=sample_assessment_id,
            collection_name=collection_name,
        )

        # Assert
        assert result == sample_question_attempts
        assert len(result) == 2
        assert result[0].question_id == "q1"
        assert result[0].is_correct is True
        assert result[1].question_id == "q2"
        assert result[1].is_correct is False
        mock_repository.get_grading_responses.assert_awaited_once_with(
            user_id=user_id,
            assessment_id=sample_assessment_id,
            collection_name=collection_name,
        )

    @pytest.mark.asyncio
    async def test_get_grading_responses_validates_response_structure(
        self,
        grading_service,
        mock_repository,
        sample_assessment_id,
        sample_question_attempts,
    ):
        """Test that the response structure matches the expected QuestionAttempt format."""
        # Arrange
        user_id = "test_user"
        collection_name = "test_collection"
        mock_repository.get_grading_responses.return_value = sample_question_attempts

        # Act
        result = await grading_service.get_grading_responses(
            user_id=user_id,
            assessment_id=sample_assessment_id,
            collection_name=collection_name,
        )

        # Assert
        # Verify first attempt structure
        attempt1 = result[0]
        assert isinstance(attempt1, GradedResponse)
        assert hasattr(attempt1, "question_id")
        assert hasattr(attempt1, "user_id")
        assert hasattr(attempt1, "attempts_remaining")
        assert hasattr(attempt1, "created_at")
        assert hasattr(attempt1, "feedback")
        assert hasattr(attempt1, "grading_version")
        assert hasattr(attempt1, "is_correct")
        assert hasattr(attempt1, "question_metadata")
        assert hasattr(attempt1, "question_type")
        assert hasattr(attempt1, "score")

        # Verify feedback structure
        feedback = attempt1.feedback
        assert isinstance(feedback, ResponseFeedback)
        assert hasattr(feedback, "message")
        assert hasattr(feedback, "explanation")
        assert hasattr(feedback, "steps")
        assert hasattr(feedback, "hint")
        assert hasattr(feedback, "show_solution")
        assert hasattr(feedback, "misconception")

    @pytest.mark.asyncio
    async def test_get_grading_responses_empty_result(
        self, grading_service, mock_repository, sample_assessment_id
    ):
        """Test retrieving grading responses when none exist."""
        # Arrange
        user_id = "test_user"
        collection_name = "test_collection"
        mock_repository.get_grading_responses.return_value = []

        # Act
        result = await grading_service.get_grading_responses(
            user_id=user_id,
            assessment_id=sample_assessment_id,
            collection_name=collection_name,
        )

        # Assert
        assert result == []
        assert len(result) == 0
        mock_repository.get_grading_responses.assert_awaited_once()

    def test_get_service_factory_method(self):
        """Test the factory method creates a properly configured service instance."""
        # Arrange
        collection_name = "test_factory_collection"

        # Act
        with patch(
            "src.repository.grading_response_repository.mongo_response_repository.MongoGradingResponseRepository.get_repo",
            return_value=MagicMock(spec=AbstractGradingResponseRepository),
        ) as mock_get_repo:
            service = GradingResponseService.get_service(collection_name)

            # Assert
            assert isinstance(service, GradingResponseService)
            assert service.collection_name == collection_name
            mock_get_repo.assert_called_once()

    @pytest.mark.asyncio
    async def test_to_dict_conversion_in_grading_response(
        self, sample_grading_response
    ):
        """Test that the to_dict method in GradingResponse works correctly."""
        # Act
        result_dict = sample_grading_response.to_dict()

        # Assert
        assert isinstance(result_dict, dict)
        assert "question_metadata" in result_dict
        assert "success" in result_dict
        assert "is_correct" in result_dict
        assert "score" in result_dict
        assert "feedback" in result_dict
        assert "attempts_remaining" in result_dict
        assert "question_type" in result_dict

        # Check feedback conversion
        feedback_dict = result_dict["feedback"]
        assert isinstance(feedback_dict, dict)
        assert "message" in feedback_dict
        assert "explanation" in feedback_dict
        assert "steps" in feedback_dict
        assert "hint" in feedback_dict
        assert "show_solution" in feedback_dict
        assert "misconception" in feedback_dict

    @pytest.mark.asyncio
    async def test_exception_handling_in_save_grading_response(
        self,
        grading_service,
        mock_repository,
        sample_grading_response,
        sample_assessment_id,
    ):
        """Test exception handling in save_grading_response method."""
        # Arrange
        user_id = "test_user"
        question_id = "test_question"
        assessment_id = sample_assessment_id

        # Setup mock to raise an exception
        mock_repository.save_grading_response.side_effect = Exception(
            "Database connection error"
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await grading_service.save_grading_response(
                user_id=user_id,
                question_id=question_id,
                assessment_id=assessment_id,
                grading_response=sample_grading_response,
            )

        assert "Database connection error" in str(exc_info.value)
        mock_repository.save_grading_response.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_exception_handling_in_get_grading_responses(
        self, grading_service, mock_repository, sample_assessment_id
    ):
        """Test exception handling in get_grading_responses method."""
        # Arrange
        user_id = "test_user"
        collection_name = "test_collection"

        # Setup mock to raise an exception
        mock_repository.get_grading_responses.side_effect = Exception(
            "Database query error"
        )

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await grading_service.get_grading_responses(
                user_id=user_id,
                assessment_id=sample_assessment_id,
                collection_name=collection_name,
            )

        assert "Database query error" in str(exc_info.value)
        mock_repository.get_grading_responses.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_save_with_none_optional_parameters(
        self,
        grading_service,
        mock_repository,
        sample_grading_response,
        sample_assessment_id,
    ):
        """Test that saving works correctly when optional parameters are None."""
        # Arrange
        user_id = "test_user"
        question_id = "test_question"
        assessment_id = sample_assessment_id

        # Modify the feedback to have None values
        modified_feedback = Feedback(
            message="Test message",
            explanation=None,
            steps=None,
            hint=None,
            show_solution=False,
            misconception=None,
        )

        modified_response = GradingResponse(
            question_metadata=sample_grading_response.question_metadata,
            success=sample_grading_response.success,
            is_correct=sample_grading_response.is_correct,
            score=sample_grading_response.score,
            feedback=modified_feedback,
            attempts_remaining=sample_grading_response.attempts_remaining,
            question_type=None,  # Test with None question_type
        )

        # Act
        result = await grading_service.save_grading_response(
            user_id=user_id,
            question_id=question_id,
            assessment_id=assessment_id,
            grading_response=modified_response,
        )

        # Assert
        assert result is True
        mock_repository.save_grading_response.assert_awaited_once()
        # Verify that None values are correctly handled
        saved_args = mock_repository.save_grading_response.call_args.kwargs
        assert saved_args["response"].feedback.explanation is None
        assert saved_args["response"].feedback.steps is None
        assert saved_args["response"].feedback.hint is None
        assert saved_args["response"].feedback.misconception is None
        assert saved_args["response"].question_type is None
