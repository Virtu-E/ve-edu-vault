from abc import abstractmethod, ABC
from typing import Optional

from ai_core.validator.registry import ValidatorRegistry


class ValidatorEngineInterface(ABC):
    @abstractmethod
    def run_all_validators(self, **kwargs) -> Optional[str]:
        raise NotImplementedError


class ValidationEngine:
    """Engine for running validations."""

    def run_all_validators(self, **kwargs) -> Optional[str]:
        """
        Run all registered validator and return first error encountered.
        Args:
            **kwargs: Arguments to pass to validator constructors
        Returns:
            Optional[str]: Error message if any validator fails, None if all pass
        """
        for validator_class in ValidatorRegistry.get_all_validators().values():
            try:
                validator_instance = validator_class(**kwargs)
                result = validator_instance.validate()

                if isinstance(result, str):  # Validation failed with error message
                    return f"{validator_class.__name__} failed: {result}"
                elif not result:  # Validation failed without message
                    return f"{validator_class.__name__} failed"

            except Exception as e:
                return f"{validator_class.__name__} error: {str(e)}"

        return None  # All validations passed
