from typing import Dict

import pytest

from ai_core.performance.calculators.base_calculator import BasePerformanceCalculator
from course_ware.tests.course_ware_factory import QuestionMetadataFactory
from data_types.ai_core import PerformanceStats
from data_types.course_ware_schema import QuestionMetadata


class TestBasePerformanceCalculator:
    @pytest.fixture
    def calculator(self) -> BasePerformanceCalculator:
        """Fixture providing a BasePerformanceCalculator instance."""
        return BasePerformanceCalculator(required_correct_questions=2)

    @pytest.fixture
    def sample_question_data(self) -> Dict[str, QuestionMetadata]:
        """Fixture providing sample question data."""
        questions = [QuestionMetadataFactory(question_id=f"q{i}", difficulty="easy", is_correct=True, attempt_number=1) for i in range(3)]
        questions.extend([QuestionMetadataFactory(question_id=f"q{i}", difficulty="medium", is_correct=i < 2, attempt_number=2) for i in range(3, 6)])
        questions.extend([QuestionMetadataFactory(question_id=f"q{i}", difficulty="hard", is_correct=False, attempt_number=3) for i in range(6, 9)])

        return {q.question_id: q for q in questions}

    def test_initialization(self, calculator: BasePerformanceCalculator):
        """Test calculator initialization with default values."""
        assert calculator.required_correct_questions == 2
        assert calculator.difficulties == ["easy", "medium", "hard"]
        assert calculator.status_values == {True: "completed", False: "incomplete"}

    def test_validate_difficulty_valid(self, calculator: BasePerformanceCalculator):
        """Test difficulty validation with valid values."""
        for difficulty in ["easy", "medium", "hard"]:
            calculator.validate_difficulty(difficulty)  # Should not raise

    def test_validate_difficulty_invalid(self, calculator: BasePerformanceCalculator):
        """Test difficulty validation with invalid values."""
        with pytest.raises(ValueError) as exc_info:
            calculator.validate_difficulty("invalid")
        assert "Invalid difficulty" in str(exc_info.value)

    def test_calculate_performance_empty_data(self, calculator: BasePerformanceCalculator):
        """Test performance calculation with empty data."""
        stats = calculator.calculate_performance({})
        assert isinstance(stats, PerformanceStats)
        assert all(status == "incomplete" for status in stats.difficulty_status.values())
        assert len(stats.ranked_difficulties) == 3
        assert all(avg == 0.0 for _, avg in stats.ranked_difficulties)

    def test_calculate_performance_complete_data(self, calculator: BasePerformanceCalculator, sample_question_data: Dict[str, QuestionMetadata]):
        """Test performance calculation with complete data."""
        stats = calculator.calculate_performance(sample_question_data)

        # Test difficulty status
        assert stats.difficulty_status["easy"] == "completed"  # 3 correct questions
        assert stats.difficulty_status["medium"] == "incomplete"  # 0 correct questions
        assert stats.difficulty_status["hard"] == "incomplete"  # 0 correct questions

        # Test ranked difficulties
        difficulties = [d for d, _ in stats.ranked_difficulties]
        assert "easy" in difficulties
        assert "medium" in difficulties
        assert "hard" in difficulties

        # Verify ranking order (by attempt number)
        avg_attempts = [avg for _, avg in stats.ranked_difficulties]
        assert avg_attempts == sorted(avg_attempts)

    def test_calculate_performance_partial_data(self, calculator: BasePerformanceCalculator):
        """Test performance calculation with partial difficulty data."""
        questions = [QuestionMetadataFactory(difficulty="easy", is_correct=True, attempt_number=1) for _ in range(2)]
        data = {q.question_id: q for q in questions}

        stats = calculator.calculate_performance(data)
        assert stats.difficulty_status["easy"] == "completed"
        assert stats.difficulty_status["medium"] == "incomplete"
        assert stats.difficulty_status["hard"] == "incomplete"

    @pytest.mark.parametrize("required_correct", [5, 1, 3])
    def test_different_required_correct_thresholds(self, required_correct: int, sample_question_data: Dict[str, QuestionMetadata]):
        """Test performance calculation with different required correct question thresholds."""
        calculator = BasePerformanceCalculator(required_correct_questions=required_correct)
        stats = calculator.calculate_performance(sample_question_data)

        # For easy difficulty (3 correct questions)
        expected_easy_status = "completed" if required_correct <= 3 else "incomplete"
        assert stats.difficulty_status["easy"] == expected_easy_status

        # For medium difficulty (0 correct questions)
        expected_medium_status = "incomplete"
        assert stats.difficulty_status["medium"] == expected_medium_status

    def test_ranking_with_equal_attempts(self, calculator: BasePerformanceCalculator):
        """Test difficulty ranking when attempt numbers are equal."""
        questions = []
        for diff in ["easy", "medium", "hard"]:
            questions.extend(
                [
                    QuestionMetadataFactory(
                        difficulty=diff,
                        is_correct=True,
                        attempt_number=2,  # Same attempt number for all
                    )
                    for _ in range(2)
                ]
            )

        data = {q.question_id: q for q in questions}
        stats = calculator.calculate_performance(data)

        # Verify all average attempts are equal
        avg_attempts = [avg for _, avg in stats.ranked_difficulties]
        assert len(set(avg_attempts)) == 1  # All values should be the same
