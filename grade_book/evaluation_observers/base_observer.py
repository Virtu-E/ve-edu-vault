from abc import ABC, abstractmethod

from data_types.ai_core import EvaluationResult


class EvaluationObserver(ABC):
    """Abstract observer that processes a specific side effect after evaluation"""

    @abstractmethod
    async def process_async(self, evaluation_result: EvaluationResult) -> None:
        """Process a specific side effect based on evaluation result"""
        raise NotImplementedError("Abstract method not implemented")
