from abc import ABC, abstractmethod
from typing import Dict


class DatabaseSync(ABC):
    """Abstract base class for database synchronization"""

    @abstractmethod
    def sync(self, structure: Dict) -> None:
        pass
