import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from bson import ObjectId
from bson.binary import UUID_SUBTYPE, Binary

from src.edu_vault.settings import common
from src.lib.grade_book_v2.question_grading.qn_grading_types import GradingResponse
from src.repository.databases.no_sql_database.mongodb import (
    AsyncMongoDatabaseEngine,
    mongo_database,
)
from src.repository.grading_response_repository.base_response_repository import (
    AbstractGradingResponseRepository,
)
from src.repository.grading_response_repository.response_data_types import (
    QuestionAttempt,
)

log = logging.getLogger(__name__)


class MongoGradingResponseRepository(AbstractGradingResponseRepository):
    """MongoDB implementation of the AbstractGradingResponseRepository."""

    __slots__ = ("database_engine", "database_name")

    def __init__(
        self,
        database_engine: AsyncMongoDatabaseEngine,
        database_name: str,
    ) -> None:
        self.database_engine = database_engine
        self.database_name = database_name
        log.info(
            "Initialized MongoGradingResponseRepository with database '%s'",
            database_name,
        )

    async def save_grading_response(
        self,
        user_id: str,
        question_id: str,
        assessment_id: UUID,
        response: GradingResponse,
        collection_name: str,
    ) -> bool:
        """Save a grading response to the database.

        Args:
            user_id: The ID of the user
            question_id: The ID of the question
            assessment_id: The ID of the assessment
            response: The GradingResponse object
            collection_name: The collection to save to

        Returns:
            bool: True if successful, False otherwise
        """
        # Convert the GradingResponse to a dictionary
        response_dict = {
            "user_id": user_id,
            "question_id": ObjectId(question_id),
            "assessment_id": Binary(assessment_id.bytes, UUID_SUBTYPE),
            "success": response.success,
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
    ) -> List[QuestionAttempt]:

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
            QuestionAttempt(**{**attempt, "question_id": str(attempt["question_id"])})
            for attempt in all_grading_responses
        ]

        return converted_data

    @classmethod
    def get_repo(cls):
        """Factory method to create a repository instance with the correct settings.

        Returns:
            MongoGradingResponseRepository: A configured repository instance
        """
        database_name = getattr(common, "NO_SQL_GRADING_RESPONSE_DATABASE_NAME", None)
        if database_name is None:
            log.error(
                "NO_SQL_GRADING_RESPONSE_DATABASE_NAME not configured in settings"
            )
            # TODO: raise custom error exception here for better details
            raise RuntimeError(
                "NO_SQL_GRADING_RESPONSE_DATABASE_NAME not configured in settings"
            )

        log.info("Creating MongoGradingResponseRepository instance")

        return MongoGradingResponseRepository(
            database_engine=mongo_database,
            database_name=database_name,
        )
