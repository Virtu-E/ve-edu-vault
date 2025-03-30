from abc import ABC, abstractmethod


class CreationSideEffect(ABC):
    """Abstract base class for creation side effects."""

    @abstractmethod
    def process_creation_side_effects(self) -> None:
        raise NotImplementedError
