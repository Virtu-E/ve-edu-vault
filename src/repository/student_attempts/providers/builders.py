import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List

from bson import ObjectId
from bson.binary import UUID_SUBTYPE, Binary

from .data_types import AttemptBuildContext, BulkAttemptBuildContext

logger = logging.getLogger(__name__)


class AttemptDataBuilder(ABC):
    """Abstract interface for building attempt data"""

    @abstractmethod
    def build(self, context: AttemptBuildContext) -> Dict[str, Any]:
        pass


class BulkAttemptDataBuilder(ABC):
    """Abstract interface for building bulk attempt data"""

    @abstractmethod
    def build(self, context: BulkAttemptBuildContext) -> List[Dict[str, Any]]:
        pass


class BulkUnansweredAttemptBuilder(BulkAttemptDataBuilder):
    """Strategy for building bulk attempt data for unanswered questions"""

    def build(self, context: BulkAttemptBuildContext) -> List[Dict[str, Any]]:
        current_time = datetime.now(timezone.utc)
        documents = []

        logger.debug(
            f"Creating bulk unanswered attempt records for user: {context.user_id}, "
            f"questions count: {len(context.unanswered_questions)}"
        )

        for question in context.unanswered_questions:
            attempt = {
                "is_correct": False,
                "score": context.default_score,
                "timestamp": current_time,
            }
            document = {
                "user_id": context.user_id,
                "question_id": ObjectId(question.id),
                "assessment_id": Binary(context.assessment_id.bytes, UUID_SUBTYPE),
                "created_at": current_time,
                "question_type": question.question_type,
                "topic": question.topic,
                "sub_topic": question.sub_topic,
                "learning_objective": question.learning_objective,
                "first_attempt_at": None,
                "last_attempt_at": None,
                "question_metadata": question.model_dump(),
                "attempts": [attempt],
                "total_attempts": 0,
                "best_score": context.default_score,
                "latest_score": context.default_score,
                "mastered": False
                and context.default_score >= context.config.mastery_threshold,
            }

            documents.append(document)

        logger.debug(f"Generated {len(documents)} bulk attempt documents")
        return documents


class FirstAttemptBuilder(AttemptDataBuilder):
    """Strategy for building first attempt data"""

    def build(self, context: AttemptBuildContext) -> Dict[str, Any]:
        current_time = datetime.now(timezone.utc)

        attempt = {
            "is_correct": context.is_correct,
            "score": context.score,
            "timestamp": current_time,
        }

        logger.debug(
            f"Creating first attempt record for user: {context.user_id}, question: {context.question.id}"
        )

        return {
            "$push": {"attempts": attempt},
            "$setOnInsert": {
                "user_id": context.user_id,
                "question_id": ObjectId(context.question.id),
                "created_at": current_time,
                "question_type": context.question.question_type,
                "topic": context.question.topic,
                "sub_topic": context.question.sub_topic,
                "learning_objective": context.question.learning_objective,
                "first_attempt_at": current_time,
                "question_metadata": context.question.model_dump(),
            },
            "$set": {
                "total_attempts": 1,
                "best_score": context.score,
                "latest_score": context.score,
                "mastered": context.is_correct
                and context.score >= context.config.mastery_threshold,
                "last_attempt_at": current_time,
            },
        }


class SubsequentAttemptBuilder(AttemptDataBuilder):
    """Strategy for building subsequent attempt data"""

    def build(self, context: AttemptBuildContext) -> Dict[str, Any]:
        current_time = datetime.now(timezone.utc)

        attempt = {
            "is_correct": context.is_correct,
            "score": context.score,
            "timestamp": current_time,
        }

        total_attempts = (
            context.existing_attempt.total_attempts + 1
            if context.existing_attempt
            else 1
        )

        logger.debug(
            f"Updating existing attempt record for user: {context.user_id}, "
            f"question: {context.question.id}, attempt #: {total_attempts}"
        )

        update_operation = {
            "$push": {"attempts": attempt},
            "$inc": {"total_attempts": 1},
            "$set": {"latest_score": context.score, "last_attempt_at": current_time},
        }

        return update_operation
