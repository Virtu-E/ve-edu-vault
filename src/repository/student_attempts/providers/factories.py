import logging
from typing import Optional

from ..mongo.attempts_repo import MongoAttemptRepository
from .attempt_provider import StudentAttemptProvider
from .builders import (
    AttemptDataBuilder,
    BulkAttemptDataBuilder,
    BulkUnansweredAttemptBuilder,
    FirstAttemptBuilder,
    SubsequentAttemptBuilder,
)
from .bulk_attempt_provider import BulkAttemptProvider
from .data_types import GradingConfig

logger = logging.getLogger(__name__)


class AttemptDataBuilderFactory:
    """Factory for creating appropriate attempt data builders"""

    @staticmethod
    def get_builder(has_existing_attempt: bool) -> AttemptDataBuilder:
        if has_existing_attempt:
            return SubsequentAttemptBuilder()
        return FirstAttemptBuilder()

    @staticmethod
    def get_bulk_builder() -> BulkAttemptDataBuilder:
        return BulkUnansweredAttemptBuilder()


class StudentAttemptProviderFactory:
    """
    Factory for creating student attempt management providers.

    Provides convenient methods for creating properly configured provider instances
    with consistent repository and configuration setup.
    """

    @staticmethod
    def create_mongo_attempt_provider(
        collection_name: str, grading_config: Optional[GradingConfig] = None
    ) -> StudentAttemptProvider:
        """
        Create a MongoDB-backed student attempt provider.

        Args:
            collection_name: Database collection name
            grading_config: Optional grading configuration

        Returns:
            Configured StudentAttemptProvider instance
        """
        logger.info(
            f"Creating StudentAttemptProvider with collection: {collection_name}"
        )

        return StudentAttemptProvider(
            attempt_repository=MongoAttemptRepository.get_repo(),
            collection_name=collection_name,
            grading_config=grading_config,
        )

    @staticmethod
    def create_mongo_bulk_provider(
        collection_name: str, grading_config: Optional[GradingConfig] = None
    ) -> BulkAttemptProvider:
        """
        Create a MongoDB-backed bulk attempt provider.

        Args:
            collection_name: Database collection name
            grading_config: Optional grading configuration

        Returns:
            Configured BulkAttemptProvider instance
        """
        logger.info(f"Creating BulkAttemptProvider with collection: {collection_name}")

        return BulkAttemptProvider(
            attempt_repository=MongoAttemptRepository.get_repo(),
            collection_name=collection_name,
            grading_config=grading_config,
        )

    @staticmethod
    def create_mongo_providers(
        collection_name: str, grading_config: Optional[GradingConfig] = None
    ) -> tuple[StudentAttemptProvider, BulkAttemptProvider]:
        """
        Create both attempt and bulk processing providers together.

        Args:
            collection_name: Database collection name
            grading_config: Optional grading configuration

        Returns:
            Tuple of (StudentAttemptProvider, BulkAttemptProvider)
        """
        attempt_provider = StudentAttemptProviderFactory.create_mongo_attempt_provider(
            collection_name, grading_config
        )
        bulk_provider = StudentAttemptProviderFactory.create_mongo_bulk_provider(
            collection_name, grading_config
        )

        return attempt_provider, bulk_provider
