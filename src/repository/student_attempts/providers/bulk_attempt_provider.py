import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from bson.binary import UUID_SUBTYPE, Binary

from src.repository.question_repository.data_types import Question
from src.repository.student_attempts.data_types import StudentQuestionAttempt
from src.repository.student_attempts.mongo.attempts_repo import MongoAttemptRepository
from src.repository.student_attempts.providers.data_types import (
    BulkAttemptBuildContext,
    GradingConfig,
)

logger = logging.getLogger(__name__)


class BulkAttemptProvider:
    """
    Provider for bulk processing of student attempts.

    Provides access to mass operations for creating and managing
    multiple attempt records efficiently.
    """

    def __init__(
        self,
        attempt_repository: MongoAttemptRepository,
        collection_name: str,
        grading_config: Optional[GradingConfig] = None,
    ) -> None:
        """
        Initialize bulk attempt provider.

        Args:
            attempt_repository: Repository for data access
            collection_name: Database collection name
            grading_config: Configuration for grading behavior
        """
        self.attempt_repository = attempt_repository
        self.collection_name = collection_name
        self.grading_config = grading_config or GradingConfig()

        logger.info(
            f"BulkAttemptProvider initialized with collection: {collection_name}"
        )

    def _build_bulk_unanswered_documents(
        self,
        student_user_id: str,
        unanswered_questions: List[Question],
        assessment_id: UUID,
    ) -> List[Dict[str, Any]]:
        """
        Build document structures for bulk unanswered question insertion.

        Args:
            student_user_id: Student's unique identifier
            unanswered_questions: List of questions not attempted
            assessment_id: Assessment's unique identifier

        Returns:
            List of documents ready for bulk insertion
        """
        if not unanswered_questions:
            return []

        bulk_context = BulkAttemptBuildContext(
            user_id=student_user_id,
            unanswered_questions=unanswered_questions,
            assessment_id=assessment_id,
            config=self.grading_config,
            default_score=0.0,
            is_correct=False,
        )

        # avoding circular imports
        from src.repository.student_attempts.providers.factories import (
            AttemptDataBuilderFactory,
        )

        bulk_builder = AttemptDataBuilderFactory.get_bulk_builder()
        return bulk_builder.build(bulk_context)

    async def bulk_create_unanswered_attempts(
        self,
        student_user_id: str,
        assessment_id: UUID,
        unanswered_questions: List[Question],
    ) -> int:
        """
        Create attempt records for all unanswered questions in bulk.

        Args:
            student_user_id: Student's unique identifier
            assessment_id: Assessment's unique identifier
            unanswered_questions: List of questions not attempted

        Returns:
            Number of attempt records created
        """
        logger.info(
            f"Starting bulk creation of unanswered attempts for user: {student_user_id}, "
            f"assessment: {assessment_id}, total questions: {len(unanswered_questions)}"
        )

        documents_to_insert = self._build_bulk_unanswered_documents(
            student_user_id=student_user_id,
            unanswered_questions=unanswered_questions,
            assessment_id=assessment_id,
        )

        if not documents_to_insert:
            logger.info(f"No documents to insert for user: {student_user_id}")
            return 0

        bulk_insertion_result = await self.attempt_repository.save_bulk_attempt(
            data=documents_to_insert,
            collection_name=self.collection_name,
        )

        records_created = len(documents_to_insert) if bulk_insertion_result else 0

        logger.info(
            f"Bulk creation completed for user: {student_user_id}. "
            f"Created {records_created} unanswered attempt records"
        )

        return records_created

    async def get_bulk_qn_attempts(
        self, user_id: int, assessment_id: UUID
    ) -> List[StudentQuestionAttempt]:
        """Retrieves 1 to many student question attempts."""
        query = {
            "user_id": user_id,
            "assessment_id": Binary(assessment_id.bytes, UUID_SUBTYPE),
        }

        return await self.attempt_repository.get_question_attempt_by_custom_query(
            self.collection_name, query
        )
