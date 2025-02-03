import pytest
from unittest.mock import Mock

from ai_core.contextual_analyzer.context_engine import ContextEngine
from course_ware.tests.course_ware_factory import TopicFactory, UserQuestionAttemptsFactory, UserQuestionSetFactory
from data_types.ai_core import LearningHistory, ModeData, DifficultyStats, QuestionAIContext, Attempt
from repository.ai_core import LearningHistoryRepository
from repository.shared import QuestionRepository


@pytest.fixture
def mock_difficulty_stats():
    return {"easy": DifficultyStats(totalAttempts=10, successRate=0.8, averageTime=120.0, failedTags=["algebra", "geometry"], firstAttemptSuccessRate=0.7, secondAttemptSuccessRate=0.8, thirdAttemptSuccessRate=0.9, averageAttemptsToSuccess=1.5, completionRate=0.9, incompleteRate=0.1, earlyAbandonment=0.05, averageFirstAttemptTime=100.0, averageSecondAttemptTime=90.0, averageThirdAttemptTime=80.0, timeDistribution={"0-5min": 0.3, "5-10min": 0.7})}


@pytest.fixture
def mock_repositories():
    question_repo = Mock(spec=QuestionRepository)
    learning_history_repo = Mock(spec=LearningHistoryRepository)
    learning_history_repo.get_learning_history.return_value = LearningHistory(userId="test_user", block_id="test_topic", modeHistory={})
    return question_repo, learning_history_repo


@pytest.fixture
def mock_builders(mock_difficulty_stats):
    context_builder = Mock()
    stats_calculator = Mock()

    question_contexts = [QuestionAIContext(_id="q1", difficulty="easy", tags=["algebra"], attempts=Attempt(success=True, timeSpent=120, attemptNumber=1))]

    context_builder.build_question_context.return_value = question_contexts
    stats_calculator.calculate.return_value = mock_difficulty_stats["easy"]

    return context_builder, stats_calculator


@pytest.fixture
def context_setup(user, mock_repositories, mock_builders):
    question_repo, learning_history_repo = mock_repositories
    context_builder, stats_calculator = mock_builders

    topic = TopicFactory()
    question_attempt = UserQuestionAttemptsFactory(user=user, current_learning_mode="normal")
    question_set = UserQuestionSetFactory(user=user)

    context_engine = ContextEngine(user=user, topic=topic, user_question_attempt=question_attempt, user_question_set=question_set, question_repository=question_repo, learning_history_repository=learning_history_repo, context_builder=context_builder, stats_calculator=stats_calculator)

    return {"engine": context_engine, "repositories": (question_repo, learning_history_repo), "builders": (context_builder, stats_calculator), "question_set": question_set, "question_attempt": question_attempt}


@pytest.mark.django_db
class TestContextEngine:
    def test_generate_learning_history_success(self, context_setup):
        """
        Tests successful generation of learning history context with proper initialization
        of ModeData, QuestionAIContext and DifficultyStats objects.
        """
        context_engine = context_setup["engine"]
        learning_history_repo = context_setup["repositories"][1]
        context_builder = context_setup["builders"][0]
        question_set = context_setup["question_set"]
        question_attempt = context_setup["question_attempt"]

        result = context_engine.generate_learning_history_context()

        assert isinstance(result, LearningHistory)
        assert "normal" in result.modeHistory
        mode_data = result.modeHistory["normal"][-1]
        assert isinstance(mode_data.questions[0], QuestionAIContext)
        assert isinstance(mode_data.difficultyStats["easy"], DifficultyStats)

        learning_history_repo.save_learning_history.assert_called_once()
        context_builder.build_question_context.assert_called_once_with(question_set.question_list_ids, question_attempt.get_latest_question_metadata)

    def test_generate_learning_history_error(self, context_setup):
        """
        Tests error handling when learning history repository encounters database error.
        """
        context_engine = context_setup["engine"]
        learning_history_repo = context_setup["repositories"][1]

        learning_history_repo.get_learning_history.side_effect = Exception("Database error")

        with pytest.raises(Exception) as exc_info:
            context_engine.generate_learning_history_context()
        assert str(exc_info.value) == "Database error"

    def test_difficulty_stats_calculation(self, context_setup, mock_difficulty_stats):
        """
        Tests calculation and validation of difficulty statistics in generated learning history.
        """
        context_engine = context_setup["engine"]
        stats_calculator = context_setup["builders"][1]

        result = context_engine.generate_learning_history_context()

        mode_data = result.modeHistory["normal"][-1]
        assert isinstance(mode_data, ModeData)
        assert isinstance(mode_data.difficultyStats["easy"], DifficultyStats)
        assert mode_data.difficultyStats["easy"] == mock_difficulty_stats["easy"]
        assert stats_calculator.calculate.call_count == 1
