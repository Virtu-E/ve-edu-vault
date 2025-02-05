from typing import Union

from ai_core.validator.base_validator import BaseValidator
from course_ware.models import UserQuestionSet, UserQuestionAttempts


class QuestionSetMetadataValidator(BaseValidator):
    """
    Validates that the number of questions in the metadata matches the question set count

    Args:
        question_set: The question set to validate against
        attempt_instance: The attempt instance containing question metadata

    Returns:
        Union[bool, str]: True if counts match, error message string if they don't match
    """

    def __init__(self, question_set: UserQuestionSet, attempt_instance: UserQuestionAttempts):
        self.question_set = question_set
        self.attempt_instance = attempt_instance

    def validate(self) -> Union[bool, str]:
        set_question_count = len(self.question_set.question_list_ids)
        metadata = self.attempt_instance.get_latest_question_metadata
        metadata_question_count = len(metadata.keys())

        if set_question_count == metadata_question_count:
            return True

        return f"Question count mismatch: {set_question_count} questions in set but {metadata_question_count} in metadata."
