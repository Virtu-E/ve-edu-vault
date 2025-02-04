# test_failed_tags_collector.py
import pytest

from ai_core.contextual_analyzer.stats.tags_collector import FailedTagsCollector
from ai_core.tests.ai_core_factories import QuestionAIContextFactory, AttemptsFactory


@pytest.fixture
def collector():
    return FailedTagsCollector()


class TestFailedTagsCollector:
    def test_empty_questions_list(self, collector):
        """Test with an empty questions list."""
        result = collector.collect_failed_tags([])
        assert result == []

    def test_no_failed_questions(self, collector):
        """Test when all questions are successful."""
        questions = [
            QuestionAIContextFactory(tags=["python", "loops"], attempts=AttemptsFactory(success=True)),
            QuestionAIContextFactory(tags=["javascript", "arrays"], attempts=AttemptsFactory(success=True)),
        ]

        result = collector.collect_failed_tags(questions)
        assert result == []

    def test_all_questions_failed(self, collector):
        """Test when all questions failed."""
        questions = [
            QuestionAIContextFactory(tags=["python", "loops"], attempts=AttemptsFactory(success=False)),
            QuestionAIContextFactory(tags=["javascript", "arrays"], attempts=AttemptsFactory(success=False)),
        ]

        result = collector.collect_failed_tags(questions)
        # Check that all tags are present
        assert set(result) == {"python", "loops", "javascript", "arrays"}

    def test_mixed_success_and_failure(self, collector):
        """Test with a mix of successful and failed questions."""
        questions = [
            QuestionAIContextFactory(tags=["python", "loops"], attempts=AttemptsFactory(success=True)),
            QuestionAIContextFactory(tags=["javascript", "arrays"], attempts=AttemptsFactory(success=False)),
        ]

        result = collector.collect_failed_tags(questions)
        # Only tags from failed question should be present
        assert set(result) == {"javascript", "arrays"}

    def test_duplicate_tags_across_questions(self, collector):
        """Test handling of duplicate tags across different questions."""
        questions = [
            QuestionAIContextFactory(tags=["python", "algorithms"], attempts=AttemptsFactory(success=False)),
            QuestionAIContextFactory(
                tags=["algorithms", "data-structures"],
                attempts=AttemptsFactory(success=False),
            ),
        ]

        result = collector.collect_failed_tags(questions)
        # Duplicate tags should appear only once
        assert set(result) == {"python", "algorithms", "data-structures"}
        assert len(result) == len(set(result))  # No duplicates

    def test_empty_tags_list(self, collector):
        """Test with questions that have empty tags lists."""
        questions = [
            QuestionAIContextFactory(tags=[], attempts=AttemptsFactory(success=False)),
            QuestionAIContextFactory(tags=["python"], attempts=AttemptsFactory(success=False)),
        ]

        result = collector.collect_failed_tags(questions)
        assert result == ["python"]

    def test_special_characters_in_tags(self, collector):
        """Test handling of tags containing special characters."""
        questions = [
            QuestionAIContextFactory(tags=["c++", "object-oriented"], attempts=AttemptsFactory(success=False)),
            QuestionAIContextFactory(
                tags=["#python", "machine-learning"],
                attempts=AttemptsFactory(success=False),
            ),
        ]

        result = collector.collect_failed_tags(questions)
        assert set(result) == {"c++", "object-oriented", "#python", "machine-learning"}

    def test_case_sensitivity(self, collector):
        """Test that tags maintain their case sensitivity."""
        questions = [
            QuestionAIContextFactory(
                tags=["Python", "python", "PYTHON"],
                attempts=AttemptsFactory(success=False),
            )
        ]

        result = collector.collect_failed_tags(questions)
        # All different cases should be preserved
        assert set(result) == {"Python", "python", "PYTHON"}
