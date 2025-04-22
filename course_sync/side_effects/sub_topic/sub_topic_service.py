import logging
from typing import Any, Dict, List, Optional, Type, TypedDict

from oauth_clients.edx_client import EdxClient
from oauth_clients.services import OAuthClient
from repository.question_respository import MongoQuestionRepository

logger = logging.getLogger(__name__)


class QuestionId(TypedDict):
    id: str


class SubTopicService:
    """Service for handling subtopic-related operations."""

    def __init__(
        self,
        question_repo: Type[MongoQuestionRepository] = MongoQuestionRepository,
        edx_client_class: Type[EdxClient] = EdxClient,
    ):
        """
        Initialize the SubTopicService.

        Args:
            question_repo: Repository for question data operations
            edx_client_class: Class used to create EdX client instances
        """
        self._question_repo = question_repo.get_repo()
        self._edx_client_class = edx_client_class
        logger.debug("SubTopicService initialized")

    async def get_question_aggregated_data(
        self,
        collection_name: str,
        examination_level: str,
        academic_class: str,
        subtopic_name: str,
        topic_name: str,
    ) -> List[QuestionId]:
        """
        Retrieve aggregated question data based on specified filters.

        Args:
            collection_name: Name of the collection to query
            examination_level: The examination level filter
            academic_class: The academic class filter
            subtopic_name: The subtopic name filter
            topic_name: The topic name filter

        Returns:
            List of question IDs matching the filter criteria
        """
        logger.info(
            "Fetching questions for topic=%s, subtopic=%s, class=%s, level=%s",
            topic_name,
            subtopic_name,
            academic_class,
            examination_level,
        )

        results = await self._question_repo.get_questions_by_aggregation(
            collection_name=collection_name,
            examination_level=examination_level,
            academic_class=academic_class,
            subtopic_name=subtopic_name,
            topic_name=topic_name,
        )

        question_list_ids = [QuestionId(id=str(question.id)) for question in results]
        logger.debug("Retrieved %d questions", len(question_list_ids))

        return question_list_ids

    async def get_course_blocks(self, block_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve course blocks from EdX by block ID.

        Args:
            block_id: ID of the block to retrieve

        Returns:
            Dictionary containing course block data or None if not found
        """
        logger.info("Fetching course blocks for block_id=%s", block_id)

        async with OAuthClient(service_type="OPENEDX") as client:
            edx_client = self._edx_client_class(client)
            results = await edx_client.get_course_blocks(block_id)

            if results:
                logger.debug("Successfully retrieved course blocks")
            else:
                logger.warning("No course blocks found for block_id=%s", block_id)

            return results
