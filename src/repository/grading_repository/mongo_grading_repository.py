import logging
from typing import Any, Dict, Optional
from uuid import UUID

from bson import ObjectId
from bson.binary import UUID_SUBTYPE, Binary

from src.edu_vault.settings import common
from src.repository.databases.no_sql_database.mongodb import (
    AsyncMongoDatabaseEngine,
    mongo_database,
)
from src.repository.grading_repository.base_grading_repository import (
    AbstractGradingRepository,
)
from src.repository.grading_repository.grading_data_types import StudentQuestionAttempt

log = logging.getLogger(__name__)


class MongoGradingRepository(AbstractGradingRepository):
    """
    MongoDB implementation of the grading repository.

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
        Initialize the MongoDB grading repository.

        Args:
            database_engine (AsyncMongoDatabaseEngine): Engine for MongoDB operations
            database_name (str): Name of the MongoDB database to use
        """
        self.database_engine = database_engine
        self.database_name = database_name
        log.info("Initialized MongoGradingRepository with database '%s'", database_name)

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

    @classmethod
    def get_repo(cls):
        """
        Factory method to create and configure a MongoGradingRepository instance.

        Returns:
            MongoGradingRepository: Configured repository instance

        Raises:
            RuntimeError: If database name is not configured in settings
        """
        database_name = getattr(common, "NO_SQL_GRADING_DATABASE_NAME", None)
        if database_name is None:
            log.error("NO_SQL_GRADING_DATABASE_NAME not configured in settings")
            # TODO : raise custom error exception here for better details
            raise RuntimeError(
                "NO_SQL_GRADING_DATABASE_NAME not configured in settings"
            )

        log.info(
            "Creating MongoGradingRepository instance with database %s", database_name
        )

        return MongoGradingRepository(
            database_engine=mongo_database,
            database_name=database_name,
        )
