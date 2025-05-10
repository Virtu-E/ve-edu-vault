from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from data_types.ai_core import EvaluationResult


class LearningHistoryRepositoryMixin(ABC):
    """
    Mixin that provides an interface for learning history operations.

    This mixin defines the contract for storing and retrieving a user's
    learning progress and evaluation results.
    """

    @abstractmethod
    def save_learning_history(
        self,
        user_id: str,
        block_id: str,
        evaluation_result: EvaluationResult,
        timestamp: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Save a learning history entry with evaluation results.

        Args:
            user_id: Unique identifier of the user
            block_id: Identifier of the learning block/unit
            evaluation_result: Results of the user's evaluation
            timestamp: Optional timestamp override (ISO format)
            metadata: Optional additional metadata to store

        Returns:
            True if save was successful, False otherwise

        Raises:
            RepositoryError: If the save operation fails
            ValidationError: If the provided data is invalid
        """
        raise NotImplementedError("save_learning_history is not implemented")

    @abstractmethod
    def get_learning_history(
        self,
        user_id: str,
        block_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve learning history for a user.

        Args:
            user_id: Unique identifier of the user
            block_id: Optional filter by specific learning block
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)
            limit: Maximum number of records to return

        Returns:
            List of learning history entries with evaluation results
        """
        pass
