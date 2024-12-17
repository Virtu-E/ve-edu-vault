from course_ware.models import Topic, UserCategoryProgress, UserQuestionAttempts
from data_types.questions import QuestionAttemptData
from exceptions import QuestionNotFoundError


class ProgressUpdater:
    def __init__(
        self,
        question_data: QuestionAttemptData,
    ):
        """
        Initializes the ProgressUpdater with the necessary instances.

        Args:
            question_data (QuestionAttemptData): The user's question data attempts.
        """
        self.user_question_attempt_instance = UserQuestionAttempts.objects.get(
            topic__id=question_data.topic_id
        )
        self.user_category_progress_instance = UserCategoryProgress.objects.get(
            category__id=question_data.category_id
        )
        self.topic_instance = Topic.objects.get(id=question_data.topic_id)
        self.question_id = question_data.question_id
        self.question_data = question_data

    def _update_user_question_attempt(self) -> bool:
        """
        Updates the user's question metadata every time the user attempts to answer.

        Returns:
            bool: True if the topic associated with the question is cleared, False otherwise.
        """
        question_metadata = self.user_question_attempt_instance.question_metadata

        # Ensure the question exists in the metadata
        question_data_instance = question_metadata.get(self.question_data.question_id)
        if question_data_instance is None:
            raise QuestionNotFoundError()

        # Update the question metadata if the question has never been answered correctly
        if not question_data_instance.get("is_correct", False):
            if self.question_data.is_correct:
                question_data_instance["is_correct"] = True
            else:
                question_data_instance["in_correct_count"] = (
                    question_data_instance.get("in_correct_count", 0) + 1
                )

        self.user_question_attempt_instance.save()

        # Check if the topic is cleared by verifying all
        # questions in the metadata are marked as correct
        topic_cleared = all(
            value.get("is_correct", False) for value in question_metadata.values()
        )

        return topic_cleared

    def _update_user_category_progress(self, topic_cleared: bool) -> None:
        """
        Updates a specific category's progress dynamically using properties.

        Args:
            topic_cleared (bool): Whether the topic was cleared.
        """
        if self.user_category_progress_instance.progress_percentage >= 100:
            return

        if topic_cleared:
            # Save the user category progress instance to update `last_activity`
            self.user_category_progress_instance.save()

    def _update_topic_progress(self, topic_cleared: bool) -> None:
        """
        Updates the topic progress, marking it as completed if the topic is cleared.

        Args:
            topic_cleared (bool): Whether the topic was cleared.
        """
        if topic_cleared:
            self.topic_instance.is_completed = True
            self.topic_instance.save()

    # TODO: Use this to pass the grade back to edX for a specific topic, whether it is cleared or not
    def process_updates(self) -> None:
        """
        Coordinates the updates for user question attempts, category progress, and topic progress.
        """
        topic_cleared = self._update_user_question_attempt()
        self._update_user_category_progress(topic_cleared)
        self._update_topic_progress(topic_cleared)
