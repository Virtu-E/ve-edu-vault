from typing import Any, Dict, Optional, Union

from ai_core.validator.base_validator import BaseValidator
from course_ware.models import UserQuestionAttempts


class LearningModeValidator(BaseValidator):
    """Validates if the learning mode in the attempt instance matches the metadata description.

    This validator ensures that the current learning mode of a user's question attempt
    matches the mode specified in the question's metadata for the current version.
    """

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

    def _get_metadata_mode(
        self, metadata: Dict[str, Any], version: str
    ) -> Optional[str]:
        """Safely extracts the learning mode from metadata for given version.

        Args:
            metadata: Question metadata dictionary
            version: Version key to look up

        Returns:
            Optional[str]: Learning mode if found, None otherwise
        """
        if not metadata or not version:
            return None

        version_data = metadata.get(version, {})
        return version_data.get("learning_mode")

    def validate(self) -> Union[bool, str]:
        """Validates the learning mode consistency.

        Returns:
            Union[bool, str]: True if validation passes, error message string if fails
        """
        try:
            current_learning_mode = self.attempt_instance.current_learning_mode
            if not current_learning_mode:
                return "Current learning mode is not set"

            metadata = self.attempt_instance.question_metadata_description
            if not metadata:
                return "Question metadata description is missing"

            current_version = self.attempt_instance.get_current_version
            if not current_version:
                return "Current version is not set"

            metadata_mode = self._get_metadata_mode(metadata, current_version)
            if metadata_mode is None:
                return (
                    f"Learning mode not found in metadata for version {current_version}"
                )

            if current_learning_mode == metadata_mode:
                return True

            return f"Learning mode mismatch: attempt instance has '{current_learning_mode}' but metadata specifies '{metadata_mode}' for version {current_version}"

        except AttributeError as e:
            return f"Invalid attempt instance structure: {str(e)}"
        except KeyError as e:
            return f"Missing required metadata key: {str(e)}"
        except Exception as e:
            return f"Validation error: {str(e)}"
