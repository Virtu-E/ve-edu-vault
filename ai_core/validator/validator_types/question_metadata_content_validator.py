from typing import Union

from pydantic import ValidationError

from ai_core.validator.base_validator import BaseValidator
from course_ware.models import UserQuestionAttempts
from data_types.course_ware_schema import QuestionMetadata


class QuestionMetadataValidator(BaseValidator):
    """Validates question metadata using Pydantic schema."""

    def __init__(self, user_question_attempt_instance: UserQuestionAttempts):
        if not isinstance(user_question_attempt_instance, UserQuestionAttempts):
            raise ValueError("Invalid user question attempt instance provided")
        self.attempt_instance = user_question_attempt_instance

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
        except Exception as e:
            return f"Validation error: {str(e)}"
