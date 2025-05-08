from typing import Union

from ai_core.validator.base_validator import BaseValidator
from course_ware.models import UserQuestionSet


class QuestionSetMetadataValidator(BaseValidator):
    """
    Validates that the number of questions in the metadata matches the question set count

    Args:
        question_set: The question set to validate against
        attempt_instance: The attempt instance containing question metadata

    Returns:
        Union[bool, str]: True if counts match, error message string if they don't match
    """

    def __init__(self, **kwargs):
        """Initialize with question set and attempt instance from kwargs.

        Args:
            **kwargs: Must contain:
                - question_set: UserQuestionSet instance
                - attempt_instance: UserQuestionAttempts instance

        Raises:
            ValueError: If required kwargs are missing or of invalid types
        """

        question_set = kwargs.get("question_set")
        attempt_instance = kwargs.get("user_question_attempt_instance")

        # Validate question_set
        if not question_set:
            raise ValueError("question_set not provided in kwargs")
        if not isinstance(question_set, UserQuestionSet):
            raise ValueError(
                f"Expected UserQuestionSet instance, got {type(question_set)}"
            )

        # Validate attempt_instance
        if not attempt_instance:
            raise ValueError("attempt_instance not provided in kwargs")
        # if not isinstance(attempt_instance, UserQuestionAttempts):
        #     raise ValueError(
        #         f"Expected UserQuestionAttempts instance, got {type(attempt_instance)}"
        #     )

        self.question_set = question_set
        self.attempt_instance = attempt_instance

    def validate(self) -> Union[bool, str]:
        set_question_count = len(self.question_set.question_list_ids)
        metadata = self.attempt_instance.get_latest_question_metadata
        metadata_question_count = len(metadata.keys())

        if set_question_count == metadata_question_count:
            return True

        return f"Question count mismatch: {set_question_count} questions in set but {metadata_question_count} in metadata."
