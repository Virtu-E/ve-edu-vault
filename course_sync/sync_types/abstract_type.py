from abc import ABC, abstractmethod

from course_sync.data_types import ChangeOperation


class DatabaseSync(ABC):
    """Abstract base class for database synchronization"""

    @abstractmethod
    def sync(self, operation: ChangeOperation) -> None:
        pass
