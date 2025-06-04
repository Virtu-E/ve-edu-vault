import logging
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from bson import ObjectId
from bson.binary import UUID_SUBTYPE, Binary

from src.config.django import base
from src.repository.databases.no_sql_database.mongo.mongodb import (
    AsyncMongoDatabaseEngine,
    mongo_database,
)
from src.repository.student_attempts.base_repo import AbstractAttemptRepository

from ..data_types import StudentQuestionAttempt

log = logging.getLogger(__name__)


class MongoAttemptRepository(AbstractAttemptRepository):
    """
    MongoDB implementation of the attempt repository.

    This repository handles storage and retrieval of student question attempts
    using MongoDB as the underlying database.

    Attributes:
        database_engine (AsyncMongoDatabaseEngine): Engine for MongoDB operations
        database_name (str): Name of the MongoDB database to use
    """

    __slots__ = ("database_engine", "database_name")

    def __init__(
        self,
        database_engine: AsyncMongoDatabaseEngine,
        database_name: str,
    ) -> None:
        """
        Initialize the MongoDB attempt repository.

        Args:
            database_engine (AsyncMongoDatabaseEngine): Engine for MongoDB operations
            database_name (str): Name of the MongoDB database to use
        """
        self.database_engine = database_engine
        self.database_name = database_name
        log.info("Initialized MongoAttemptRepository with database '%s'", database_name)

    async def save_attempt(
        self,
        user_id: str,
        question_id: str,
        assessment_id: UUID,
        update: Dict[str, Any],
        collection_name: str,
    ) -> bool:
        """
        Save or update a student's question attempt.

        Args:
            user_id (str): ID of the user
            question_id (str): ID of the question
            assessment_id (UUID): ID of the assessment
            update (Dict[str, Any]): Data to update
            collection_name (str): MongoDB collection name

        Returns:
            bool: True if the operation was successful
        """
        log.debug(
            "Saving question attempt for user=%s, question=%s, assessment=%s",
            user_id,
            question_id,
            assessment_id,
        )

        query = {
            "user_id": user_id,
            "question_id": ObjectId(question_id),
            "assessment_id": Binary(assessment_id.bytes, UUID_SUBTYPE),
        }

        result = await self.database_engine.update_one_to_db(
            upsert=True,
            query=query,
            update=update,
            collection_name=collection_name,
            database_name=self.database_name,
        )

        log.debug("Save attempt result: %s", result)
        return result

    async def save_bulk_attempt(
        self,
        collection_name: str,
        data: Union[Dict, list],
    ) -> bool:
        """
        Save multiple attempts to the database in bulk operation.

        Args:
            collection_name (str): MongoDB collection name
            data (Union[Dict, list]): Dictionary or list containing multiple attempt records

        Returns:
            bool: True if bulk save was successful, False otherwise
        """
        result = await self.database_engine.write_to_db(
            data=data,
            collection_name=collection_name,
            database_name=self.database_name,
        )

        log.debug("Save attempt result: %s", result)
        return result

    async def get_question_attempt_single(
        self,
        user_id: str,
        question_id: str,
        collection_name: str,
        assessment_id: UUID,
    ) -> Optional[StudentQuestionAttempt]:
        """
        Retrieve a single question attempt for a user.

        Args:
            user_id (str): ID of the user
            question_id (str): ID of the question
            collection_name (str): MongoDB collection name
            assessment_id (UUID): ID of the assessment

        Returns:
            Optional[StudentQuestionAttempt]: The question attempt if found, None otherwise
        """
        log.debug(
            "Fetching question attempt for user=%s, question=%s, assessment=%s",
            user_id,
            question_id,
            assessment_id,
        )

        query = {
            "user_id": user_id,
            "question_id": ObjectId(question_id),
            "assessment_id": Binary(assessment_id.bytes, UUID_SUBTYPE),
        }

        response = await self.database_engine.fetch_one_from_db(
            query=query,
            collection_name=collection_name,
            database_name=self.database_name,
        )

        if not response:
            log.debug("No question attempt found")
            return None

        result = response[0] if isinstance(response, list) else response
        log.debug("Found question attempt with ID: %s", result.get("_id", "unknown"))
        return StudentQuestionAttempt(**result)

    async def get_question_attempt_by_custom_query(
        self, collection_name: str, query: dict[Any, Any]
    ) -> List[StudentQuestionAttempt]:
        """
        Retrieve question attempts by a custom query.
        Args:
            collection_name: Name of the question collection/category
            query: Dictionary of question attempts query parameters
        Returns:
            List[StudentQuestionAttempt]: List of StudentQuestionAttempt objects

        """

        question_attempts = []

        async for batch in await self.database_engine.fetch_from_db(
            collection_name, self.database_name, query
        ):
            question_attempts.extend(batch)

        result = [StudentQuestionAttempt(**attempt) for attempt in question_attempts]

        return result

    async def get_question_attempts_by_aggregation(
        self, collection_name: str, pipeline: Any
    ) -> List[StudentQuestionAttempt]:
        """
        Retrieve multiple question attempts using aggregation pipeline.

        Args:
            collection_name (str): MongoDB collection name
            pipeline (Any): Aggregation pipeline for filtering/grouping

        Returns:
            List[StudentQuestionAttempt]: List of StudentQuestionAttempt objects
        """

        aggregation_results = await self.database_engine.run_aggregation(
            collection_name, self.database_name, pipeline
        )

        if not aggregation_results or not isinstance(aggregation_results, list):
            return []

        flattened_results = []
        for result in aggregation_results:
            for key, question_list in result.items():
                if isinstance(question_list, list):
                    flattened_results.extend(question_list)
                else:
                    log.warning(
                        f"Unexpected data structure in aggregation result: {key}"
                    )

        return [StudentQuestionAttempt(**result) for result in flattened_results]

    @classmethod
    def get_repo(cls):
        """
        Factory method to create and configure a MongoAttemptRepository instance.

        Returns:
            MongoAttemptRepository: Configured repository instance

        Raises:
            RuntimeError: If database name is not configured in settings
        """
        database_name = getattr(base, "NO_SQL_ATTEMPTS_DATABASE", None)
        if database_name is None:
            log.error("NO_SQL_ATTEMPTS_DATABASE not configured in settings")
            # TODO : raise custom error exception here for better details
            raise RuntimeError("NO_SQL_ATTEMPTS_DATABASE not configured in settings")

        log.info(
            "Creating MongoAttemptRepository instance with database %s", database_name
        )

        return MongoAttemptRepository(
            database_engine=mongo_database,
            database_name=database_name,
        )

    def __repr__(self):
        return (
            f"<{type(self).__name__}: {self.database_name}, {self.database_engine!r}>"
        )
