from typing import Dict, Type

from ai_core.validator.base_validator import BaseValidator
from ai_core.validator.validator_types.learning_mode_validator import LearningModeValidator
from ai_core.validator.validator_types.question_count_validator import PrerequisiteQuestionCountValidator
from ai_core.validator.validator_types.question_metadata_content_validator import QuestionMetadataValidator
from ai_core.validator.validator_types.question_set_validator import QuestionSetMetadataValidator


class ValidatorRegistry:
    """Registry for managing validator."""

    _validators: Dict[str, Type[BaseValidator]] = {}

    @classmethod
    def register(cls, validator_class: Type[BaseValidator]) -> None:
        """
        Register a new validator class.
        Args:
            validator_class: The validator class to register
        """
        if not issubclass(validator_class, BaseValidator):
            raise TypeError("Validator must inherit from OrchestrationEngineValidator")

        cls._validators[validator_class.__name__] = validator_class

    @classmethod
    def get_all_validators(cls) -> Dict[str, Type[BaseValidator]]:
        """Get all registered validator."""
        return cls._validators.copy()


ValidatorRegistry.register(LearningModeValidator)
ValidatorRegistry.register(PrerequisiteQuestionCountValidator)
ValidatorRegistry.register(QuestionMetadataValidator)
ValidatorRegistry.register(QuestionSetMetadataValidator)
