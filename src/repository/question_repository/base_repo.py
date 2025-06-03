from abc import ABC, abstractmethod
from typing import Any, List

from src.apps.learning_tools.questions.models import QuestionSet
from src.repository.question_repository.data_types import Question


class AbstractQuestionRepository(ABC):
    """
    Abstract class that provides an interface for question retrieval operations.

    This class defines the contract for accessing question data from various
    storage backends (database, cache, external APIs, etc.).
    """

    @abstractmethod
    async def get_questions_by_ids(
        self, question_ids: List[QuestionSet], collection_name: str
    ) -> List[Question]:
        """
        Retrieve multiple questions by their unique identifiers.

        Args:
            question_ids: List of question identifiers to retrieve
            collection_name: Name of the question collection/category

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
