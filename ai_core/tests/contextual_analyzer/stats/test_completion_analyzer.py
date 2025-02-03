import pytest

from ai_core.contextual_analyzer.stats.completion_analyzer import CompletionAnalyzer
from ai_core.tests.ai_core_factories import QuestionAIContextFactory, AttemptsFactory


@pytest.fixture
def analyzer():
    return CompletionAnalyzer()


class TestCompletionAnalyzer:
    def test_empty_questions_list(self, analyzer):
        """Test analysis with empty questions list."""
        result = analyzer.analyze_completion([])
        assert result == {"completionRate": 0.0, "incompleteRate": 0.0, "earlyAbandonment": 0.0}

    def test_all_questions_completed(self, analyzer):
        """Test analysis when all questions are completed successfully."""
        questions = [QuestionAIContextFactory(attempts=AttemptsFactory(success=True, attemptNumber=1)) for _ in range(3)]

        result = analyzer.analyze_completion(questions)
        assert result == {"completionRate": 100.0, "incompleteRate": 0.0, "earlyAbandonment": 0.0}

    def test_all_questions_max_attempts_failed(self, analyzer):
        """Test analysis when all questions reached max attempts but failed."""
        questions = [QuestionAIContextFactory(attempts=AttemptsFactory(success=False, attemptNumber=CompletionAnalyzer.MAX_ATTEMPTS)) for _ in range(3)]

        result = analyzer.analyze_completion(questions)
        assert result == {"completionRate": 0.0, "incompleteRate": 100.0, "earlyAbandonment": 0.0}

    def test_all_questions_early_abandoned(self, analyzer):
        """Test analysis when all questions were abandoned early."""
        questions = [QuestionAIContextFactory(attempts=AttemptsFactory(success=False, attemptNumber=1)) for _ in range(3)]

        result = analyzer.analyze_completion(questions)
        assert result == {"completionRate": 0.0, "incompleteRate": 0.0, "earlyAbandonment": 100.0}

    def test_mixed_completion_scenarios(self, analyzer):
        """Test analysis with mixed completion scenarios."""
        questions = [
            # Completed successfully
            QuestionAIContextFactory(attempts=AttemptsFactory(success=True, attemptNumber=2)),
            # Failed at max attempts
            QuestionAIContextFactory(attempts=AttemptsFactory(success=False, attemptNumber=CompletionAnalyzer.MAX_ATTEMPTS)),
            # Abandoned early
            QuestionAIContextFactory(attempts=AttemptsFactory(success=False, attemptNumber=1)),
            # Another successful completion
            QuestionAIContextFactory(attempts=AttemptsFactory(success=True, attemptNumber=1)),
        ]

        result = analyzer.analyze_completion(questions)
        assert result == {"completionRate": 50.0, "incompleteRate": 25.0, "earlyAbandonment": 25.0}

    def test_rounding_behavior(self, analyzer):
        """Test that percentages are rounded to one decimal place."""
        questions = [QuestionAIContextFactory(attempts=AttemptsFactory(success=True, attemptNumber=1)), QuestionAIContextFactory(attempts=AttemptsFactory(success=True, attemptNumber=2)), QuestionAIContextFactory(attempts=AttemptsFactory(success=False, attemptNumber=CompletionAnalyzer.MAX_ATTEMPTS))]

        result = analyzer.analyze_completion(questions)
        assert result == {"completionRate": 66.7, "incompleteRate": 33.3, "earlyAbandonment": 0.0}
