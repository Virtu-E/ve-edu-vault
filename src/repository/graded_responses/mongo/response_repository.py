import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from bson import ObjectId
from bson.binary import UUID_SUBTYPE, Binary

from src.config.django import base
from src.repository.databases.no_sql_database.mongo.mongodb import (
    AsyncMongoDatabaseEngine,
    mongo_database,
)
from src.repository.graded_responses.base_repo import AbstractGradingResponseRepository

from ..data_types import GradedResponse

logger = logging.getLogger(__name__)


class MongoGradingResponseRepository(AbstractGradingResponseRepository):
    """
    MongoDB implementation of the grading response repository.

    This repository handles storage and retrieval of graded responses
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
        Initialize the MongoDB grading response repository.

        Args:
            database_engine (AsyncMongoDatabaseEngine): Engine for MongoDB operations
            database_name (str): Name of the MongoDB database to use
        """
        self.database_engine = database_engine
        self.database_name = database_name
        logger.info(
            "Initialized MongoGradingResponseRepository with database '%s'",
            database_name,
        )

    async def save_grading_response(
        self,
        user_id: str,
        question_id: str,
        assessment_id: UUID,
        response: GradedResponse,
        collection_name: str,
    ) -> bool:
        """
        Save a grading response to the database.

        Args:
            user_id (str): The ID of the user
            question_id (str): The ID of the question
            assessment_id (UUID): The ID of the assessment
            response (GradedResponse): The GradingResponse object
            collection_name (str): The collection to save to

        Returns:
            bool: True if successful, False otherwise
        """
        # Convert the GradingResponse to a dictionary
        response_dict = {
            "user_id": user_id,
            "question_id": ObjectId(question_id),
            "assessment_id": Binary(assessment_id.bytes, UUID_SUBTYPE),
            "success": response.is_correct,
            "is_correct": response.is_correct,
            "score": response.score,
            "attempts_remaining": response.attempts_remaining,
            "question_metadata": response.question_metadata,
            "feedback": {
                "message": response.feedback.message,
                "explanation": response.feedback.explanation,
                "steps": response.feedback.steps,
                "hint": response.feedback.hint,
                "show_solution": response.feedback.show_solution,
                "misconception": response.feedback.misconception,
            },
            # Add metadata fields
            "created_at": datetime.now(timezone.utc),
            "grading_version": "1.0",
            # You can add additional context fields here or pass them as parameters if needed
            "topic": None,
            "sub_topic": None,
            "learning_objective": None,
            "question_type": response.question_type,
        }

        result = await self.database_engine.update_one_to_db(
            upsert=True,
            query={
                "user_id": user_id,
                "question_id": ObjectId(question_id),
                "assessment_id": Binary(assessment_id.bytes, UUID_SUBTYPE),
            },
            update={"$set": response_dict},
            collection_name=collection_name,
            database_name=self.database_name,
        )
        return result

    async def get_grading_responses(
        self,
        user_id: str,
        assessment_id: UUID,
        collection_name: str,
    ) -> List[GradedResponse]:
        """
        Retrieve all grading responses for a user and assessment.

        Args:
            user_id (str): The ID of the user
            assessment_id (UUID): The ID of the assessment
            collection_name (str): The collection to fetch from

        Returns:
            List[GradedResponse]: List of graded response objects
        """
        all_grading_responses = []

        # consuming entire generator content. Its contents are small
        async for batch in await self.database_engine.fetch_from_db(
            collection_name,
            self.database_name,
            query={
                "user_id": user_id,
                "assessment_id": Binary(assessment_id.bytes, UUID_SUBTYPE),
            },
        ):
            all_grading_responses.extend(batch)

        converted_data = [
            GradedResponse(**{**attempt, "question_id": str(attempt["question_id"])})
            for attempt in all_grading_responses
        ]

        return converted_data

    @classmethod
    def get_repo(cls):
        """
        Factory method to create a repository instance with the correct settings.

        Returns:
            MongoGradingResponseRepository: A configured repository instance

        Raises:
            RuntimeError: If database name is not configured in settings
        """
        database_name = getattr(base, "NO_SQL_GRADING_RESPONSE_DATABASE_NAME", None)
        if database_name is None:
            logger.error(
                "NO_SQL_GRADING_RESPONSE_DATABASE_NAME not configured in settings"
            )
            raise RuntimeError(
                "NO_SQL_GRADING_RESPONSE_DATABASE_NAME not configured in settings"
            )

        logger.info("Creating MongoGradingResponseRepository instance")

        return MongoGradingResponseRepository(
            database_engine=mongo_database,
            database_name=database_name,
        )

    def __repr__(self):
        return (
            f"<{type(self).__name__}: {self.database_name}, {self.database_engine!r}>"
        )
