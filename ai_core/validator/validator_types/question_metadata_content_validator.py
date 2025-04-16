from typing import Union

from pydantic import ValidationError

from ai_core.validator.base_validator import BaseValidator
from course_ware.models import UserQuestionAttempts
from data_types.course_ware_schema import QuestionMetadata


class QuestionMetadataValidator(BaseValidator):
    """Validates question metadata using Pydantic schema."""

    def __init__(self, **kwargs):
        """Initialize the validator with kwargs.

        Args:
            **kwargs: Keyword arguments containing user_question_attempt_instance
        """
        attempt_instance = kwargs.get("user_question_attempt_instance")

        if not attempt_instance:
            raise ValueError("user_question_attempt_instance not provided in kwargs")

        if not isinstance(attempt_instance, UserQuestionAttempts):
            raise ValueError(
                f"Expected UserQuestionAttempts instance, got {type(attempt_instance)}"
            )

        self.attempt_instance = attempt_instance

    def validate(self) -> Union[bool, str]:
        """Validates that the question metadata follows the required schema.

        Returns:
            Union[bool, str]: True if validation passes, error message string if fails
        """
        try:
            metadata = self.attempt_instance.question_metadata
            if not metadata:
                return "Question metadata is empty"

            version_content = self.attempt_instance.get_latest_question_metadata

            # Validate each question entry using Pydantic
            for question_id, entry in version_content.items():
                QuestionMetadata.model_validate(entry)

            return True

        except ValidationError as e:
            return f"Schema validation error: {str(e)}"
