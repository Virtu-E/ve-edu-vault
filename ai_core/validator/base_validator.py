from abc import ABC, abstractmethod
from typing import Union


class BaseValidator(ABC):
    """Base abstract class for all validator."""

    @abstractmethod
    def validate(self) -> Union[bool, str]:
        """
        Implement the validation logic in this method.
        Returns:
            Union[bool, str]: True if validation passes, error message string if fails
        """
        pass
