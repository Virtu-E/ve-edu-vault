from unittest.mock import Mock

import pytest

from ai_core.contextual_analyzer.stats.stats_calculator import (
    DifficultyStatsCalculator,
    QuestionFilter,
)
from ai_core.tests.ai_core_factories import QuestionAIContextFactory
from data_types.ai_core import DifficultyStats


@pytest.fixture
def mock_dependencies():
    """Fixture providing mock dependencies used for testing."""
    return {
        "question_filter": Mock(),
        "attempt_calculator": Mock(),
        "time_analyzer": Mock(),
        "completion_analyzer": Mock(),
        "tags_collector": Mock(),
    }


@pytest.fixture
def calculator(mock_dependencies):
    """Fixture providing an instance of DifficultyStatsCalculator with mocked dependencies."""
    return DifficultyStatsCalculator(
        mock_dependencies["question_filter"],
        mock_dependencies["attempt_calculator"],
        mock_dependencies["time_analyzer"],
        mock_dependencies["completion_analyzer"],
        mock_dependencies["tags_collector"],
    )


class TestDifficultyStatsCalculator:
    def test_calculate_with_no_questions(self, calculator, mock_dependencies):
        """Test calculator with no questions."""
        mock_dependencies["question_filter"].filter_by_difficulty.return_value = []
        questions = []

        result = calculator.calculate(questions, "medium")

        assert isinstance(result, DifficultyStats)
        assert result.totalAttempts == 0
        assert result.successRate == 0.0

    def test_calculate_with_no_attempts(self, calculator, mock_dependencies):
        """Test calculator with questions having no attempts recorded."""
        filtered_questions = [QuestionAIContextFactory()]
        mock_dependencies["question_filter"].filter_by_difficulty.return_value = filtered_questions
        mock_dependencies["attempt_calculator"].calculate_total_attempts.return_value = 0

        result = calculator.calculate([filtered_questions[0]], "medium")

        assert result.totalAttempts == 0
        assert result.successRate == 0.0

    def test_calculate_with_valid_data(self, calculator, mock_dependencies):
        """Test calculator with valid questions and attempts data."""
        filtered_questions = [QuestionAIContextFactory(), QuestionAIContextFactory()]
        mock_dependencies["question_filter"].filter_by_difficulty.return_value = filtered_questions

        mock_dependencies["attempt_calculator"].calculate_total_attempts.return_value = 5
        mock_dependencies["attempt_calculator"].calculate_success_rate.return_value = 0.8
        mock_dependencies["attempt_calculator"].calculate_attempt_specific_rates.return_value = {
            "first": 0.6,
            "second": 0.3,
            "third": 0.1,
        }

        mock_dependencies["time_analyzer"].analyze_time.return_value = {
            "averageFirstAttemptTime": 120.0,
            "averageSecondAttemptTime": 90.0,
            "averageThirdAttemptTime": 60.0,
            "firstAttempt": 120.0,
            "secondAttempt": 90.0,
            "thirdAttempt": 60.0,
        }

        mock_dependencies["completion_analyzer"].analyze_completion.return_value = {
            "completionRate": 0.75,
            "incompleteRate": 0.15,
            "earlyAbandonment": 0.10,
        }

        mock_dependencies["tags_collector"].collect_failed_tags.return_value = [
            "arrays",
            "sorting",
        ]

        result = calculator.calculate(filtered_questions, "medium")

        assert result.totalAttempts == 5
        assert result.successRate == 0.8
        assert result.firstAttemptSuccessRate == 0.6
        assert result.averageFirstAttemptTime == 120.0
        assert result.completionRate == 0.75
        assert result.failedTags == ["arrays", "sorting"]


class TestQuestionFilter:
    def test_filter_by_difficulty(self):
        """Test filtering questions by specified difficulty."""
        filter_instance = QuestionFilter()
        questions = [
            QuestionAIContextFactory(difficulty="easy"),
            QuestionAIContextFactory(difficulty="medium"),
            QuestionAIContextFactory(difficulty="hard"),
            QuestionAIContextFactory(difficulty="medium"),
        ]

        filtered = filter_instance.filter_by_difficulty(questions, "medium")

        assert len(filtered) == 2
        assert all(q.difficulty == "medium" for q in filtered)

    def test_filter_by_difficulty_no_matches(self):
        """Test filtering with no matching difficulty."""
        filter_instance = QuestionFilter()
        questions = [
            QuestionAIContextFactory(difficulty="easy"),
            QuestionAIContextFactory(difficulty="medium"),
        ]

        filtered = filter_instance.filter_by_difficulty(questions, "hard")

        assert len(filtered) == 0

    def test_filter_by_difficulty_empty_list(self):
        """Test filtering with an empty question list."""
        filter_instance = QuestionFilter()
        questions = []

        filtered = filter_instance.filter_by_difficulty(questions, "medium")

        assert len(filtered) == 0
