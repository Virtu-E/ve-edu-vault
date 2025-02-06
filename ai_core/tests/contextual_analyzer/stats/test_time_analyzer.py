import pytest

from ai_core.contextual_analyzer.stats.time_analyzer import TimeAnalyzer
from ai_core.tests.ai_core_factories import AttemptsFactory, QuestionAIContextFactory


@pytest.fixture
def analyzer():
    return TimeAnalyzer()


class TestTimeAnalyzer:
    def test_empty_questions_list(self, analyzer):
        """Test analysis with empty questions list."""
        result = analyzer.analyze_time([])
        assert result == {
            "averageTime": 0.0,
            "averageFirstAttemptTime": 0.0,
            "averageSecondAttemptTime": 0.0,
            "averageThirdAttemptTime": 0.0,
            "timeDistribution": {
                "firstAttempt": 0.0,
                "secondAttempt": 0.0,
                "thirdAttempt": 0.0,
            },
        }

    def test_first_attempts_only(self, analyzer):
        """Test analysis when all questions are on their first attempt."""
        questions = [
            QuestionAIContextFactory(attempts=AttemptsFactory(attemptNumber=1, timeSpent=100)),
            QuestionAIContextFactory(attempts=AttemptsFactory(attemptNumber=1, timeSpent=200)),
        ]

        result = analyzer.analyze_time(questions)
        assert result["averageFirstAttemptTime"] == 150.0  # (100 + 200) / 2
        assert result["averageSecondAttemptTime"] == 0.0
        assert result["averageThirdAttemptTime"] == 0.0
        assert result["timeDistribution"]["firstAttempt"] == 1.0
        assert result["timeDistribution"]["secondAttempt"] == 0.0
        assert result["timeDistribution"]["thirdAttempt"] == 0.0

    def test_two_attempts_per_question(self, analyzer):
        """Test analysis when questions have had two attempts."""
        questions = [
            QuestionAIContextFactory(
                attempts=AttemptsFactory(attemptNumber=2, timeSpent=150)  # Total time after 2 attempts
            ),
            QuestionAIContextFactory(
                attempts=AttemptsFactory(attemptNumber=2, timeSpent=200)  # Total time after 2 attempts
            ),
        ]

        result = analyzer.analyze_time(questions)
        # Both questions contribute to first and second attempt averages
        assert result["averageFirstAttemptTime"] == 175.0  # (150 + 200) / 2
        assert result["averageSecondAttemptTime"] == 175.0  # (150 + 200) / 2
        assert result["averageThirdAttemptTime"] == 0.0

        # Time distribution should split between first and second attempts
        assert pytest.approx(result["timeDistribution"]["firstAttempt"]) == 0.5
        assert pytest.approx(result["timeDistribution"]["secondAttempt"]) == 0.5
        assert result["timeDistribution"]["thirdAttempt"] == 0.0

    def test_mixed_attempt_counts(self, analyzer):
        """Test with questions having different numbers of attempts."""
        questions = [
            QuestionAIContextFactory(
                attempts=AttemptsFactory(attemptNumber=1, timeSpent=100)  # One attempt
            ),
            QuestionAIContextFactory(
                attempts=AttemptsFactory(attemptNumber=2, timeSpent=300)  # Two attempts
            ),
            QuestionAIContextFactory(
                attempts=AttemptsFactory(attemptNumber=3, timeSpent=600)  # Three attempts
            ),
        ]

        result = analyzer.analyze_time(questions)
        # First attempt average includes all questions
        assert result["averageFirstAttemptTime"] == (100 + 300 + 600) / 3
        # Second attempt average includes only questions with 2+ attempts
        assert result["averageSecondAttemptTime"] == (300 + 600) / 2
        # Third attempt average includes only questions with 3 attempts
        assert result["averageThirdAttemptTime"] == 600.0

    def test_time_distribution_with_varied_attempts(self, analyzer):
        """Test time distribution calculations with varied attempt counts."""
        questions = [
            QuestionAIContextFactory(attempts=AttemptsFactory(attemptNumber=1, timeSpent=100)),
            QuestionAIContextFactory(
                attempts=AttemptsFactory(attemptNumber=2, timeSpent=300)  # 150 per attempt average
            ),
            QuestionAIContextFactory(
                attempts=AttemptsFactory(attemptNumber=3, timeSpent=600)  # 200 per attempt average
            ),
        ]

        result = analyzer.analyze_time(questions)
        total_time = 1000  # 100 + 300 + 600

        # Time distribution should be proportional to time spent in each attempt phase
        expected_first = (100 + 150 + 200) / total_time
        expected_second = (150 + 200) / total_time
        expected_third = 200 / total_time

        assert pytest.approx(result["timeDistribution"]["firstAttempt"]) == expected_first
        assert pytest.approx(result["timeDistribution"]["secondAttempt"]) == expected_second
        assert pytest.approx(result["timeDistribution"]["thirdAttempt"]) == expected_third

    def test_zero_time_spent(self, analyzer):
        """Test handling of questions with zero time spent."""
        questions = [QuestionAIContextFactory(attempts=AttemptsFactory(attemptNumber=2, timeSpent=0))]

        result = analyzer.analyze_time(questions)
        assert result["averageFirstAttemptTime"] == 0.0
        assert result["averageSecondAttemptTime"] == 0.0
        assert result["timeDistribution"]["firstAttempt"] == 0.0
        assert result["timeDistribution"]["secondAttempt"] == 0.0

    @pytest.mark.parametrize(
        "attempt_number,time_spent",
        [
            (0, 100),  # Invalid attempt number
            (4, 100),  # Attempt number too high
            (1, -100),  # Negative time
        ],
    )
    def test_invalid_data_handling(self, analyzer, attempt_number, time_spent):
        """Test handling of invalid attempt numbers and negative times."""
        questions = [QuestionAIContextFactory(attempts=AttemptsFactory(attemptNumber=attempt_number, timeSpent=time_spent))]

        # The analyzer should handle these cases gracefully
        result = analyzer.analyze_time(questions)
        assert isinstance(result["averageFirstAttemptTime"], float)
        assert isinstance(result["timeDistribution"]["firstAttempt"], float)

    def test_internal_time_grouping(self, analyzer):
        """Test the internal _group_time_by_attempt method."""
        questions = [
            QuestionAIContextFactory(attempts=AttemptsFactory(attemptNumber=1, timeSpent=100)),
            QuestionAIContextFactory(attempts=AttemptsFactory(attemptNumber=2, timeSpent=300)),
        ]

        time_groups = analyzer._group_time_by_attempt(questions)
        # First attempt times should include all questions
        assert time_groups["first"] == [100, 300]
        # Second attempt times should only include the question with 2 attempts
        assert time_groups["second"] == [300]
        # No third attempts
        assert time_groups["third"] == []
