import pytest
from pydantic import ValidationError

from ai_core.performance_calculators import (
    AttemptBasedDifficultyRankerCalculator,
    DifficultyStatus,
)
from course_ware.tests.course_ware_factory import QuestionMetadataFactory
from data_types.ai_core import PerformanceStats


class TestPerformanceCalculators:
    def test_empty_question_data(self, calculator, empty_question_data):
        """Test calculator behavior with empty input"""
        result = calculator.calculate_performance(empty_question_data)
        assert isinstance(result, PerformanceStats)
        assert result.ranked_difficulties == []
        assert result.difficulty_status == {}

    def test_completed_difficulty(self, calculator, completed_easy_questions):
        """Test when a difficulty level is completed"""
        result = calculator.calculate_performance(completed_easy_questions)

        assert "easy" in result.difficulty_status
        assert result.difficulty_status["easy"] == DifficultyStatus.COMPLETED.value
        # Since all questions are completed, there should be no ranked difficulties
        assert result.ranked_difficulties == []

    def test_incomplete_difficulty(self, calculator, incomplete_medium_questions):
        """Test when a difficulty level is incomplete"""
        result = calculator.calculate_performance(incomplete_medium_questions)

        assert "medium" in result.difficulty_status
        assert result.difficulty_status["medium"] == DifficultyStatus.INCOMPLETE.value
        assert len(result.ranked_difficulties) == 1
        assert result.ranked_difficulties[0][0] == "medium"
        assert isinstance(result.ranked_difficulties[0][1], float)

    def test_mixed_completion(self, calculator, mixed_hard_questions):
        """Test with mixed completion status within a difficulty level"""
        result = calculator.calculate_performance(mixed_hard_questions)

        assert "hard" in result.difficulty_status
        # With 2 correct out of 6 questions (below 2/3 threshold)
        assert result.difficulty_status["hard"] == DifficultyStatus.INCOMPLETE.value
        assert len(result.ranked_difficulties) == 1
        difficulty, avg_attempts = result.ranked_difficulties[0]
        assert difficulty == "hard"
        # Average should be between 4 and 5 attempts
        assert 4 <= avg_attempts <= 5

    def test_multiple_difficulty_levels(
        self,
        calculator,
        completed_easy_questions,
        incomplete_medium_questions,
        mixed_hard_questions,
    ):
        """Test with questions from multiple difficulty levels"""
        combined_questions = {
            **completed_easy_questions,
            **incomplete_medium_questions,
            **mixed_hard_questions,
        }

        result = calculator.calculate_performance(combined_questions)

        # easy won't be in the dataset since its completed. Only Incomplete difficulty status exists
        assert result.difficulty_status.get("easy", None) is None
        assert result.difficulty_status["medium"] == DifficultyStatus.INCOMPLETE.value
        assert result.difficulty_status["hard"] == DifficultyStatus.INCOMPLETE.value

        # Check ranking of incomplete difficulties
        assert len(result.ranked_difficulties) == 2  # medium and hard
        # Hard questions should be ranked first (more attempts)
        assert result.ranked_difficulties[0][0] == "hard"
        assert result.ranked_difficulties[1][0] == "medium"

    def test_completion_threshold(self):
        """Test the completion threshold constant"""
        calculator = AttemptBasedDifficultyRankerCalculator()
        assert calculator.COMPLETION_THRESHOLD == 2 / 3

    @pytest.mark.parametrize(
        "difficulty,is_correct,expected_status",
        [
            (
                "easy",
                ["true"] * 7 + ["false"] * 3,  # 70% correct - should be completed
                DifficultyStatus.COMPLETED.value,
            ),
            (
                "medium",
                ["true"] * 6 + ["false"] * 4,  # 60% correct - should be incomplete
                DifficultyStatus.INCOMPLETE.value,
            ),
            (
                "hard",
                ["true"] * 3 + ["false"] * 7,  # 30% correct - should be incomplete
                DifficultyStatus.INCOMPLETE.value,
            ),
        ],
    )
    def test_completion_threshold_boundaries(
        self, calculator, difficulty, is_correct, expected_status
    ):
        """Test various completion rates around the threshold"""
        questions = {
            f"q{i}": QuestionMetadataFactory(
                difficulty=difficulty, is_correct=is_correct[i], attempt_number=1
            )
            for i in range(len(is_correct))
        }

        result = calculator.calculate_performance(questions)
        assert result.difficulty_status[difficulty] == expected_status

    def test_edge_case_single_question(self, calculator):
        """Test behavior with a single question"""
        questions = {
            "q1": QuestionMetadataFactory(
                difficulty="easy", is_correct="true", attempt_number=1
            )
        }

        result = calculator.calculate_performance(questions)
        assert "easy" in result.difficulty_status
        assert result.difficulty_status["easy"] == DifficultyStatus.COMPLETED.value
        assert result.ranked_difficulties == []

    def test_invalid_difficulty_values(self, calculator):
        """Test handling of invalid difficulty values"""
        questions = {
            "q1": QuestionMetadataFactory(
                difficulty="invalid_difficulty",  # Invalid difficulty
                is_correct="true",
                attempt_number=1,
            )
        }
        # TODO : maybe add a function to handle gracefully ?
        with pytest.raises(ValidationError):
            calculator.calculate_performance(questions)
