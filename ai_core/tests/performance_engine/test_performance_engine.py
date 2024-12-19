from unittest.mock import patch

import pytest

from ai_core.tests.performance_engine.performance_engine_factory import (
    QuestionMetadataFactory,
    UserQuestionAttemptsFactory,
)
from data_types.ai_core import PerformanceStats


class TestPerformanceEngine:
    def test_parse_version_valid(self, performance_engine):
        """Test parsing valid version strings"""
        assert performance_engine._parse_version("v1.0.0") == (1, 0, 0)
        assert performance_engine._parse_version("v2.1.3") == (2, 1, 3)

    def test_parse_version_invalid(self, performance_engine):
        """Test parsing invalid version strings"""
        with pytest.raises(ValueError):
            performance_engine._parse_version("invalid")
        with pytest.raises(ValueError):
            performance_engine._parse_version("v1.a.0")

    def test_get_current_question_version(self, performance_engine):
        """Test getting the latest version from question metadata"""
        question_metadata = {
            "v1.0.0": {
                "question1": QuestionMetadataFactory().__dict__,
            },
            "v2.0.0": {
                "question2": QuestionMetadataFactory().__dict__,
            },
        }

        latest_version = performance_engine._get_current_question_version(
            question_metadata, performance_engine._parse_version
        )

        assert latest_version == question_metadata["v2.0.0"]

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

        result = performance_engine._get_user_attempt_question_metadata()
        assert isinstance(result, dict)
        assert "v1.0.0" in result
        assert "v2.0.0" in result

    def test_get_user_attempt_question_metadata_not_found(self, performance_engine):
        """Test getting question metadata when user attempts don't exist"""
        result = performance_engine._get_user_attempt_question_metadata()
        assert result == {}

    def test_get_user_attempt_question_metadata_error(self, performance_engine):
        """Test handling errors when retrieving question metadata"""
        with patch(
            "course_ware.models.UserQuestionAttempts.objects.get",
            side_effect=Exception("Test error"),
        ):
            result = performance_engine._get_user_attempt_question_metadata()
            assert result == {}

    def test_get_current_question_version_invalid_metadata(self, performance_engine):
        """Test handling invalid metadata in get_current_question_version"""
        invalid_metadata = {"invalid_version": {}, "also_invalid": {}}

        with pytest.raises(ValueError):
            performance_engine._get_current_question_version(
                invalid_metadata, performance_engine._parse_version
            )

    def test_default_question_metadata(self, performance_engine, user, topic):
        """Test that new UserQuestionAttempts instances have default metadata"""
        user_attempt = UserQuestionAttemptsFactory(
            user=user,
            topic=topic,
            question_metadata={"v1.0.0": {}},  # Using the default value
        )

        assert user_attempt.question_metadata == {"v1.0.0": {}}
