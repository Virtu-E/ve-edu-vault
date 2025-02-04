# tests/factories.py
from unittest.mock import Mock, patch

import pytest

from ai_core.performance.performance_engine import PerformanceEngine
from course_ware.tests.course_ware_factory import UserQuestionAttemptsFactory
from data_types.ai_core import PerformanceStats
from exceptions import DatabaseQueryError


@pytest.fixture
def mock_performance_calculator():
    calculator = Mock()
    calculator.calculate_performance.return_value = PerformanceStats(
        ranked_difficulties=[("easy", 1.5), ("medium", 2.3), ("hard", 4.0)],
        difficulty_status={
            "easy": "completed",
            "medium": "completed",
            "hard": "incomplete",
        },
    )
    return calculator


@pytest.fixture
def performance_engine(mock_performance_calculator, user, topic):
    return PerformanceEngine(
        topic_id=topic.id,
        user_id=user.id,
        performance_calculator=mock_performance_calculator,
    )


class TestPerformanceEngine:
    def test_get_topic_performance_stats_with_data(self, performance_engine, user, topic):
        UserQuestionAttemptsFactory(
            user_id=user.id,
            topic_id=topic.id,
        )

        result = performance_engine.get_topic_performance_stats()

        assert isinstance(result, PerformanceStats)
        assert result.ranked_difficulties == [
            ("easy", 1.5),
            ("medium", 2.3),
            ("hard", 4.0),
        ]
        assert result.difficulty_status == {
            "easy": "completed",
            "medium": "completed",
            "hard": "incomplete",
        }

    def test_get_topic_performance_stats_no_data(self, performance_engine):
        result = performance_engine.get_topic_performance_stats()

        assert isinstance(result, PerformanceStats)
        assert result.ranked_difficulties == []
        assert result.difficulty_status == {}

    def test_get_user_attempt_question_metadata_success(self, performance_engine, user, topic):
        question_attempt = UserQuestionAttemptsFactory(user_id=user.id, topic_id=topic.id)

        instance = performance_engine._get_user_attempt_question_attempt_instance()

        assert instance == question_attempt

    def test_get_user_attempt_question_metadata_not_found(self, performance_engine):
        instance = performance_engine._get_user_attempt_question_attempt_instance()

        assert instance is None

    @patch("course_ware.models.UserQuestionAttempts.objects.get", autospec=True)
    def test_get_user_attempt_question_metadata_error(self, mock_get, performance_engine):
        mock_get.side_effect = Exception("Database error")

        with pytest.raises(DatabaseQueryError):
            performance_engine._get_user_attempt_question_attempt_instance()
