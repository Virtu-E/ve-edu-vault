from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from data_types.ai_core import EvaluationResult

from .data_types import Question


class QuestionRepositoryMixin(ABC):
    """
    Mixin that provides an interface for question retrieval operations.

    This mixin defines the contract for accessing question data from various
    storage backends (database, cache, external APIs, etc.).
    """

    @abstractmethod
    async def get_questions_by_ids(
        self, question_ids: List[str], collection_name: str
    ) -> List[Question]:
        """
        Retrieve multiple questions by their unique identifiers.

        Args:
            question_ids: List of question identifiers to retrieve
            collection_name: Name of the question collection/category
            **kwargs: Additional parameters for the retrieval operation

        Returns:
            List of Question objects matching the provided identifiers

        Raises:
            QuestionNotFoundError: If any questions cannot be found
            RepositoryConnectionError: If the underlying storage cannot be accessed
        """
        raise NotImplementedError("get_questions_by_ids is not implemented")

    @abstractmethod
    async def get_question_by_single_id(
        self, question_id: str, collection_name: str
    ) -> Question:
        """
        Retrieve a single question by its unique identifier.

        Args:
            question_id: Unique identifier of the question
            collection_name: Name of the question collection/category

        Returns:
            The Question object or None if not found

        Raises:
            RepositoryConnectionError: If the underlying storage cannot be accessed
        """
        raise NotImplementedError("get_question_by_single_id is not implemented")

    @abstractmethod
    async def get_question_by_custom_query(
        self, collection_name: str, query: dict[Any, Any]
    ) -> List[Question]:
        """
        Retrieve questions by a custom query.
        Args:
            collection_name: Name of the question collection/category
            query: Dictionary of question query parameters
        Returns:
            List of Question objects matching the provided identifiers

        """
        raise NotImplementedError("get_question_by_custom_query is not implemented")

    @abstractmethod
    async def get_questions_by_aggregation(
        self, collection_name: str, pipeline: Any
    ) -> List[Question]:
        """
         Retrieve and process questions using a MongoDB aggregation pipeline.

        Args:
            collection_name: Name of the collection to query
            pipeline: MongoDB aggregation pipeline

        Returns:
            List of processed Question objects
        """
        raise NotImplementedError("get_questions_by_aggregation is not implemented")


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


class QuestionAttemptRepositoryMixin(ABC):
    pass
