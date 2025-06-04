from unittest.mock import Mock

import pytest

from src.repository.graded_responses.data_types import StudentAnswer
from src.repository.question_repository.data_types import Question

from ..grader_factory import GraderFactory, GraderTypeEnum
from ..grader_types.base import AbstractQuestionGrader
from ..grader_types.multiple_choice import MultipleChoiceGrader


class TestGraderFactory:
    @pytest.fixture(autouse=True)
    def reset_graders(self):
        """Reset the graders dictionary before each test to ensure isolation."""
        # Store original graders to restore after the test
        original_graders = GraderFactory._graders.copy()
        # Clear the graders
        GraderFactory._graders = {}
        # Re-register the default grader
        GraderFactory.register_grader(
            GraderTypeEnum.MULTIPLE_CHOICE, MultipleChoiceGrader
        )

        yield

        # Restore original state after test
        GraderFactory._graders = original_graders

    def test_register_grader_adds_to_registry(self):
        """Test that a grader can be registered correctly."""

        # Arrange
        class TestGrader(AbstractQuestionGrader):
            def grade(self, question, attempted_answer):
                return True

            def calculate_score(self, is_correct):
                return 1.0 if is_correct else 0.0

        # Act
        GraderFactory.register_grader("test-type", TestGrader)

        # Assert
        assert "test-type" in GraderFactory._graders
        assert GraderFactory._graders["test-type"] == TestGrader

    def test_get_grader_returns_instance_of_registered_class(self):
        """Test that get_grader returns an instance of the registered class."""
        # Act
        grader = GraderFactory.get_grader("multiple-choice")

        # Assert
        assert isinstance(grader, MultipleChoiceGrader)

    def test_get_grader_returns_new_instance_each_call(self):
        """Test that each call to get_grader returns a new instance."""
        # Act
        grader1 = GraderFactory.get_grader("multiple-choice")
        grader2 = GraderFactory.get_grader("multiple-choice")

        # Assert
        assert grader1 is not grader2
        assert isinstance(grader1, MultipleChoiceGrader)
        assert isinstance(grader2, MultipleChoiceGrader)

    def test_register_grader_overrides_existing_type(self):
        """Test that registering a grader for an existing type overrides it."""

        # Arrange
        class NewMultipleChoiceGrader(AbstractQuestionGrader):
            def grade(self, question, attempted_answer):
                return True

            def calculate_score(self, is_correct):
                return 100.0 if is_correct else 0.0

        # Create mock question and attempted answer
        mock_question = Mock(spec=Question)
        mock_answer = Mock(spec=StudentAnswer)

        # Act
        GraderFactory.register_grader(
            GraderTypeEnum.MULTIPLE_CHOICE, NewMultipleChoiceGrader
        )
        grader = GraderFactory.get_grader("multiple-choice")

        # Assert
        assert isinstance(grader, NewMultipleChoiceGrader)
        assert not isinstance(grader, MultipleChoiceGrader)
        assert grader.grade(mock_question, mock_answer) is True
        assert grader.calculate_score(True) == 100.0
