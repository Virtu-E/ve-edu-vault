from abc import ABC, abstractmethod


class UniqueValidator(ABC):
    """
    Abstract class for Unique validators.
    """

    @abstractmethod
    def event_is_unique(self, event_id: str) -> bool:
        raise NotImplementedError()


# TODO : finish implementing this
class WebhookUniqueValidator(UniqueValidator):
    def __init__(self, event_id: str):
        pass
