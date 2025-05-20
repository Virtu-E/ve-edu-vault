import pytest

from src.repository.question_repository.tests.factories import (
    EmptyOptionsContentFactory,
    NoCorrectOptionsQuestionFactory,
    QuestionFactory,
    TrueFalseQuestionFactory,
)

from ..qn_graders import AbstractQuestionGrader, MultipleChoiceGrader
from .factories import AttemptedAnswerFactory


class TestMultipleChoiceGrader:
    """Test suite for the MultipleChoiceGrader class."""

    @pytest.fixture
    def grader(self):
        """Fixture to create a MultipleChoiceGrader instance."""
        return MultipleChoiceGrader()

    @pytest.fixture
    def sample_question(self):
        """Fixture to create a sample multiple-choice question using factory."""
        return QuestionFactory()

    @pytest.fixture
    def correct_answer(self):
        """Fixture for a correct answer with all correct options selected."""
        return AttemptedAnswerFactory(
            question_type="multiple-choice",
            question_metadata={"selected_option_ids": ["option1", "option4"]},
        )

    @pytest.fixture
    def partially_correct_answer(self):
        """Fixture for a partially correct answer with only some correct options selected."""
        return AttemptedAnswerFactory(
            question_type="multiple-choice",
            question_metadata={"selected_option_ids": ["option1"]},
        )

    @pytest.fixture
    def incorrect_answer(self):
        """Fixture for an incorrect answer with wrong options selected."""
        return AttemptedAnswerFactory(
            question_type="multiple-choice",
            question_metadata={"selected_option_ids": ["option2", "option3"]},
        )

    @pytest.fixture
    def mixed_answer(self):
        """Fixture for a mixed answer with both correct and incorrect options."""
        return AttemptedAnswerFactory(
            question_type="multiple-choice",
            question_metadata={"selected_option_ids": ["option1", "option2"]},
        )

    @pytest.fixture
    def empty_answer(self):
        """Fixture for an empty answer with no options selected."""
        return AttemptedAnswerFactory(
            question_type="multiple-choice",
            question_metadata={"selected_option_ids": []},
        )

    def test_grade_with_fully_correct_answer(
        self, grader, sample_question, correct_answer
    ):
        """Test grading a fully correct answer."""
        # Act
        result = grader.grade(sample_question, correct_answer)

        # Assert
        assert result is True

    def test_grade_with_partially_correct_answer(
        self, grader, sample_question, partially_correct_answer
    ):
        """Test grading a partially correct answer (missing some correct options)."""
        # Act
        result = grader.grade(sample_question, partially_correct_answer)

        # Assert
        assert result is False

    def test_grade_with_incorrect_answer(
        self, grader, sample_question, incorrect_answer
    ):
        """Test grading a completely incorrect answer."""
        # Act
        result = grader.grade(sample_question, incorrect_answer)

        # Assert
        assert result is False

    def test_grade_with_mixed_answer(self, grader, sample_question, mixed_answer):
        """Test grading an answer with both correct and incorrect options."""
        # Act
        result = grader.grade(sample_question, mixed_answer)

        # Assert
        assert result is False

    def test_grade_with_empty_answer(self, grader, sample_question, empty_answer):
        """Test grading an empty answer."""
        # Act
        result = grader.grade(sample_question, empty_answer)

        # Assert
        # This should be False since there are correct options that weren't selected
        assert result is False

    def test_grade_with_no_correct_options(self, grader):
        """Test grading when the question has no correct options."""
        # Arrange
        question = NoCorrectOptionsQuestionFactory()

        # Create an empty answer
        answer = AttemptedAnswerFactory(
            question_type="multiple-choice",
            question_metadata={"selected_option_ids": []},
        )

        # Act
        result = grader.grade(question, answer)

        # Assert
        # This should be True since no options are correct and none were selected
        assert result is True

    def test_grade_with_duplicate_selections(self, grader, sample_question):
        """Test grading when the answer contains duplicate option IDs."""
        # Arrange
        answer = AttemptedAnswerFactory(
            question_type="multiple-choice",
            question_metadata={
                "selected_option_ids": ["option1", "option1", "option4"]
            },
        )

        # Act
        result = grader.grade(sample_question, answer)

        # Assert
        # This should be True as the duplicates are removed by the set conversion
        assert result is True

    def test_calculate_score_correct(self, grader):
        """Test score calculation for correct answers."""
        # Act
        score = grader.calculate_score(True)

        # Assert
        assert score == 1.0
        assert isinstance(score, float)

    def test_calculate_score_incorrect(self, grader):
        """Test score calculation for incorrect answers."""
        # Act
        score = grader.calculate_score(False)

        # Assert
        assert score == 0.0
        assert isinstance(score, float)

    def test_inheritance_from_abstract_class(self):
        """Test that MultipleChoiceGrader properly inherits from AbstractQuestionGrader."""
        # Assert
        assert issubclass(MultipleChoiceGrader, AbstractQuestionGrader)

        # Create an instance to ensure it can be instantiated
        grader = MultipleChoiceGrader()
        assert isinstance(grader, AbstractQuestionGrader)

    def test_case_insensitive_option_ids(self, grader, sample_question):
        """Test handling of case-insensitive option IDs."""
        # Arrange
        answer = AttemptedAnswerFactory(
            question_type="multiple-choice",
            question_metadata={"selected_option_ids": ["OPTION1", "OPTION4"]},
        )

        # Act
        result = grader.grade(sample_question, answer)

        # Assert
        # This should be False as option IDs are case-sensitive
        assert result is False

    def test_order_independence(self, grader, sample_question):
        """Test that the order of selected options doesn't matter."""
        # Arrange
        answer1 = AttemptedAnswerFactory(
            question_type="multiple-choice",
            question_metadata={"selected_option_ids": ["option1", "option4"]},
        )

        answer2 = AttemptedAnswerFactory(
            question_type="multiple-choice",
            question_metadata={"selected_option_ids": ["option4", "option1"]},
        )

        # Act
        result1 = grader.grade(sample_question, answer1)
        result2 = grader.grade(sample_question, answer2)

        # Assert
        assert result1 is True
        assert result2 is True
        assert result1 == result2

    def test_grade_with_malformed_content(self, grader):
        """Test handling question with empty options list."""
        # Arrange
        # Create a question with empty options
        question = QuestionFactory(content=EmptyOptionsContentFactory())

        # Create a standard answer
        answer = AttemptedAnswerFactory(
            question_type="multiple-choice",
            question_metadata={"selected_option_ids": ["option1"]},
        )

        # Act
        result = grader.grade(question, answer)

        # Assert
        # With no options, there are no correct answers to select,
        # so an answer with selections should be incorrect
        assert result is False

    def test_grade_with_malformed_answer(self, grader, sample_question):
        """Test handling malformed answer without required metadata."""
        # Arrange
        malformed_answer = AttemptedAnswerFactory(
            question_type="multiple-choice",
            question_metadata={},  # Missing selected_option_ids
        )

        # Act & Assert
        with pytest.raises(KeyError):
            grader.grade(sample_question, malformed_answer)

    def test_grade_with_invalid_option_ids(self, grader, sample_question):
        """Test grading when the answer contains option IDs that don't exist in the question."""
        # Arrange
        answer = AttemptedAnswerFactory(
            question_type="multiple-choice",
            question_metadata={"selected_option_ids": ["option1", "option999"]},
        )

        # Act
        result = grader.grade(sample_question, answer)

        # Assert
        # This should be False as one of the selected options doesn't exist
        assert result is False

    def test_single_option_question(self, grader):
        """Test grading a single-option question (true/false type)."""
        # Arrange
        # Create a true/false question using factory
        question = TrueFalseQuestionFactory()

        # Create a correct answer
        correct_answer = AttemptedAnswerFactory(
            question_type="multiple-choice",
            question_metadata={"selected_option_ids": ["true"]},
        )

        # Create an incorrect answer
        incorrect_answer = AttemptedAnswerFactory(
            question_type="multiple-choice",
            question_metadata={"selected_option_ids": ["false"]},
        )

        # Act
        correct_result = grader.grade(question, correct_answer)
        incorrect_result = grader.grade(question, incorrect_answer)

        # Assert
        assert correct_result is True
        assert incorrect_result is False
