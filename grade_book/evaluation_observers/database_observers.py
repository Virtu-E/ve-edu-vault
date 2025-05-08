from asgiref.sync import sync_to_async

from ai_core.performance.data_types import PerformanceStatsData
from course_ware.models import EdxUser, SubTopic, UserQuestionSet
from course_ware_ext.models import TopicMastery
from data_types.ai_core import EvaluationResult
from grade_book.evaluation_observers.base_observer import EvaluationObserver


class UserAttemptObserver(EvaluationObserver):
    """Updates user attempt based on evaluation result"""

    def __init__(self, user_attempt):
        self._user_attempt = user_attempt

    async def process_async(self, evaluation_result: EvaluationResult) -> None:
        """Update user attempt with new learning mode and metadata"""
        next_version = self._user_attempt.get_next_version
        self._user_attempt.current_learning_mode = evaluation_result.next_mode.mode_name
        self._user_attempt.question_metadata[next_version] = {}
        self._user_attempt.question_metadata_description[next_version] = {
            "status": "Completed" if evaluation_result.passed else "Not Started",
            "learning_mode": evaluation_result.next_mode.mode_name,
            "guidance": evaluation_result.next_mode.guidance,
            "mode_guidance": evaluation_result.next_mode.mode_guidance,
        }

        self._user_attempt.current_learning_mode = evaluation_result.next_mode
        await sync_to_async(self._user_attempt.save)()


class UserQuestionSetObserver(EvaluationObserver):
    """Updates user question set based on evaluation result"""

    def __init__(self, user_question_set: UserQuestionSet):
        self._user_question_set = user_question_set

    async def process_async(self, evaluation_result: EvaluationResult) -> None:
        """Update user question set for next questions"""
        # The next question set for the user will come from AI recommendation
        # TODO: make sure that the function that assigns the base question set to the user questions set does not fire
        self._user_question_set.question_list_ids = [{}]
        await sync_to_async(self._user_question_set.save)()


class TopicMasteryObserver(EvaluationObserver):
    """Updates topic mastery based on evaluation result"""

    def __init__(
        self,
        sub_topic: SubTopic,
        user: EdxUser,
        performance_stats: PerformanceStatsData,
    ):
        self._topic = sub_topic
        self._user = user
        self._performance_stats = performance_stats

    async def process_async(self, evaluation_result: EvaluationResult) -> None:
        """Update topic mastery status and points"""

        get_or_create = sync_to_async(TopicMastery.objects.get_or_create)
        topic_mastery, _ = await get_or_create(topic=self._topic, user=self._user)

        num_failed_difficulties = len(self._performance_stats.failed_difficulties)
        total_difficulties = 3
        points_per_difficulty = (
            100 // total_difficulties
        )  # Each difficulty level is worth 33 points

        if evaluation_result.passed and num_failed_difficulties == 0:
            topic_mastery.points_earned = 100
            topic_mastery.mastery_status = "mastered"
        else:
            points_earned = (
                total_difficulties - num_failed_difficulties
            ) * points_per_difficulty
            topic_mastery.points_earned = points_earned
            topic_mastery.mastery_status = "in_progress"

        await sync_to_async(topic_mastery.save)()


class LearningHistoryObserver(EvaluationObserver):
    """Records learning history based on evaluation result"""

    def __init__(self, user: EdxUser, sub_topic: SubTopic):
        self._user = user
        self._topic = sub_topic

    async def process_async(self, evaluation_result: EvaluationResult) -> None:
        """Save learning history"""
        # TODO: Implement learning history recording logic
        pass
