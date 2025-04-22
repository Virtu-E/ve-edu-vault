import asyncio
import logging
from typing import Dict, List

from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist

from course_sync.side_effects.sub_topic.default_question_side_effect import (
    DefaultQuestionSetAssignerMixin,
)
from course_sync.side_effects.sub_topic.iframe_id_side_effect import (
    SubtopicIframeAssociatorMixin,
)
from course_sync.side_effects.sub_topic.sub_topic_service import SubTopicService
from course_ware.models import SubTopic

logger = logging.getLogger(__name__)


class SubTopicCreationSideEffect(
    DefaultQuestionSetAssignerMixin, SubtopicIframeAssociatorMixin
):
    """Class to handle all related creation side effects in relation to a subtopic instance."""

    def __init__(
        self,
        subtopic: SubTopic,
        subtopic_service=None,
    ) -> None:
        """
        Initialize the SubTopicCreationSideEffect.

        Args:
            subtopic: The subtopic instance to process
            subtopic_service: Service for subtopic operations (optional)
        """
        # Refresh subtopic instance to ensure we have latest data
        try:
            self._subtopic = subtopic
            self._subtopic_service = subtopic_service or SubTopicService()
        except ObjectDoesNotExist:
            logger.error("SubTopic not found during initialization", exc_info=True)
            raise

        logger.info(
            "Initialized SubTopicCreationSideEffect for subtopic: %s (ID: %s)",
            self._subtopic.name,
            self._subtopic.id,
        )

    async def process_creation_side_effects(self) -> None:
        """Process all side effects related to subtopic creation."""
        try:
            logger.info(
                "Starting creation side effects for subtopic: %s", self._subtopic.name
            )

            collection_name = await sync_to_async(
                lambda: self._subtopic.topic.course.course_key
            )()

            # Execute both network calls concurrently
            logger.debug("Starting concurrent network operations")
            question_data_task = self._get_question_data(collection_name)
            course_blocks_task = self._subtopic_service.get_course_blocks(
                self._subtopic.block_id
            )

            question_list_ids, course_blocks = await asyncio.gather(
                question_data_task, course_blocks_task
            )
            logger.debug("Completed concurrent network operations")

            # Process the results
            logger.debug("Creating default question set")
            await self.sync_question_set(question_list_ids, self._subtopic)

            if course_blocks:
                logger.debug("Associating iframe with subtopic")
                await self.associate_iframe_with_subtopic(course_blocks, self._subtopic)
            else:
                logger.warning(
                    "No course blocks found for block ID: %s",
                    self._subtopic.block_id,
                )

            logger.info(
                "Successfully completed all creation side effects for subtopic: %s",
                self._subtopic.name,
            )

        except ObjectDoesNotExist as e:
            logger.error(
                "Required object not found while processing subtopic %s",
                self._subtopic.id,
                exc_info=True,
                extra={"subtopic_id": self._subtopic.id, "error": str(e)},
            )
            raise
        except asyncio.CancelledError:
            logger.warning(
                "Async operations were cancelled for subtopic %s", self._subtopic.id
            )
            raise

    async def _get_question_data(self, collection_name: str) -> List[Dict[str, str]]:
        """
        Get question data for the subtopic using SubTopicService.

        Args:
            collection_name: Name of the collection to query

        Returns:
            List of question IDs matching the filter criteria
        """
        topic = self._subtopic.topic
        examination_level = await sync_to_async(lambda: topic.examination_level.name)()
        academic_class = await sync_to_async(lambda: topic.academic_class.name)()

        question_ids = await self._subtopic_service.get_question_aggregated_data(
            collection_name=collection_name,
            examination_level=examination_level,
            academic_class=academic_class,
            subtopic_name=self._subtopic.name,
            topic_name=topic.name,
        )

        # Convert TypedDict objects to regular dictionaries for compatibility
        return [{"id": item["id"]} for item in question_ids]
