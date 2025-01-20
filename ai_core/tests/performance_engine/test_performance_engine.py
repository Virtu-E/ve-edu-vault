from unittest.mock import patch

import pytest

from course_ware.models import UserQuestionAttempts
from course_ware.tests.course_ware_factory import UserQuestionAttemptsFactory
from data_types.ai_core import PerformanceStats
from exceptions import DatabaseQueryError


class TestPerformanceEngine:

    def test_get_topic_performance_stats_with_data(
        self, performance_engine, user, topic
    ):
        """Test getting performance stats when data exists"""
        UserQuestionAttemptsFactory(
            user=user,
            topic=topic,
        )

        stats = performance_engine.get_topic_performance_stats()

        assert isinstance(stats, PerformanceStats)
        assert len(stats.ranked_difficulties) > 0
        assert len(stats.difficulty_status) > 0

    def test_get_topic_performance_stats_no_data(self, performance_engine):
        """Test getting performance stats when no data exists"""
        stats = performance_engine.get_topic_performance_stats()

        assert isinstance(stats, PerformanceStats)
        assert stats.ranked_difficulties == []
        assert stats.difficulty_status == {}

    def test_get_user_attempt_question_metadata_success(
        self, performance_engine, user, topic
    ):
        """Test successfully retrieving question metadata"""
        UserQuestionAttemptsFactory(user=user, topic=topic)

        result, user_question_attempt_instance = (
            performance_engine._get_user_attempt_question_metadata()
        )
        assert isinstance(result, dict)
        assert isinstance(user_question_attempt_instance, UserQuestionAttempts)
        assert "v1.0.0" in result
        assert "v2.0.0" in result

    def test_get_user_attempt_question_metadata_not_found(self, performance_engine):
        """Test getting question metadata when user attempts don't exist"""
        result = performance_engine._get_user_attempt_question_metadata()
        assert result == ({}, None)

    def test_get_user_attempt_question_metadata_error(self, performance_engine):
        """Test handling errors when retrieving question metadata"""
        with patch(
            "course_ware.models.UserQuestionAttempts.objects.get",
            side_effect=Exception("Test error"),
        ):
            with pytest.raises(DatabaseQueryError):
                performance_engine._get_user_attempt_question_metadata()

    def test_default_question_metadata(self, performance_engine, user, topic):
        """Test that new UserQuestionAttempts instances have default metadata"""
        user_attempt = UserQuestionAttemptsFactory(
            user=user,
            topic=topic,
            question_metadata={"v1.0.0": {}},  # Using the default value
        )

        assert user_attempt.question_metadata == {"v1.0.0": {}}
