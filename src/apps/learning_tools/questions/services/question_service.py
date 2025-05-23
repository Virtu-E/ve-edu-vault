import logging
from typing import Dict, List

from src.repository.question_repository.mongo_qn_repository import (
    MongoQuestionRepository,
)
from src.repository.question_repository.qn_repository_data_types import Question
from src.utils.mixins.question_mixin import QuestionSetResources

from ..exceptions import QuestionAttemptError, QuestionNotFoundError

logger = logging.getLogger(__name__)


class QuestionService:
    """Service for fetching and managing questions with improved error handling."""

    def __init__(self, question_repo: MongoQuestionRepository, collection_name: str):
        self._question_repo = question_repo
        self._collection_name = collection_name
        logger.info(f"QuestionService initialized for collection: {collection_name}")

    async def get_questions_from_ids(
        self, question_set_ids: List[Dict[str, str]]
    ) -> List[Dict]:
        """
        Retrieve Question objects based on question IDs and convert to dictionaries.

        Args:
            question_set_ids: List of question ID dictionaries

        Returns:
            List[Dict]: Serialized Question objects

        Raises:
            QuestionAttemptError: If questions cannot be retrieved
        """
        try:
            if not question_set_ids:
                logger.warning("Empty question_set_ids provided")
                return []

            logger.debug(
                f"Retrieving {len(question_set_ids)} questions from collection {self._collection_name}"
            )

            questions = await self._question_repo.get_questions_by_ids(
                collection_name=self._collection_name, question_ids=question_set_ids
            )

            if not questions:
                logger.warning("No questions found for provided IDs")
                return []

            dumped_questions = [question.model_dump() for question in questions]
            logger.info(f"Successfully retrieved {len(dumped_questions)} questions")
            return dumped_questions

        except Exception as e:
            logger.error(f"Failed to retrieve questions: {e}")
            raise QuestionAttemptError(
                "Failed to retrieve questions from database"
            ) from e

    async def get_question_by_id(self, question_id: str) -> Question:
        """
        Retrieve a Question object by ID.

        Args:
            question_id: Unique identifier for the question

        Returns:
            Question: The retrieved question

        Raises:
            QuestionNotFoundError: If question is not found
            QuestionAttemptError: If retrieval fails
        """
        try:
            if not question_id:
                raise QuestionNotFoundError("Question ID cannot be empty")

            logger.debug(
                f"Retrieving question {question_id} from collection {self._collection_name}"
            )

            question = await self._question_repo.get_question_by_single_id(
                collection_name=self._collection_name, question_id=question_id
            )

            if not question:
                raise QuestionNotFoundError(
                    f"Question {question_id} not found in collection {self._collection_name}"
                )

            logger.debug(f"Successfully retrieved question: {question_id}")
            return question

        except QuestionNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve question {question_id}: {e}")
            raise QuestionAttemptError(
                f"Database error retrieving question {question_id}"
            ) from e

    @classmethod
    def get_service(cls, resource_context: QuestionSetResources) -> "QuestionService":
        collection_name = resource_context.resources.collection_name
        question_repo = MongoQuestionRepository.get_repo()
        return cls(question_repo, collection_name)
