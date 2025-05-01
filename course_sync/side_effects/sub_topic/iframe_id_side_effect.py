import logging
from typing import Any, Dict, Optional

from asgiref.sync import sync_to_async

from course_ware.models import SubTopic, SubTopicIframeID

logger = logging.getLogger(__name__)


class SubtopicIframeAssociatorMixin:
    """Mixin class that assigns appropriate LTI iframe identifiers to subtopics"""

    async def associate_iframe_with_subtopic(
        self, course_blocks: Dict[str, Any], subtopic: SubTopic
    ) -> None:
        """
        Creates or updates the subtopic's iframe ID when an LTI consumer is available.

        Args:
            course_blocks: Course structure containing block information
            subtopic: The subtopic to associate with an iframe ID
        """
        try:
            if course_blocks:
                iframe_id, display_name = self._extract_lti_consumer_id(course_blocks)
                if iframe_id:
                    # TODO : to be deprecated, in favor of learning objective
                    await sync_to_async(SubTopicIframeID.objects.update_or_create)(
                        sub_topic=subtopic, defaults={"identifier": iframe_id}
                    )
                    # TODO : to be deprecated
                    # await sync_to_async(LearningObjective.objects.update_or_create)(
                    #     sub_topic=subtopic,
                    #     defaults={"iframe_id": iframe_id, "name": display_name},
                    # )
                else:
                    logger.warning("No iframe ID found for subtopic %s", subtopic.name)
            else:
                logger.warning(
                    "No course blocks available for subtopic %s", subtopic.name
                )

        except SubTopic.DoesNotExist:
            logger.error(
                "Failed to associate iframe ID with subtopic %s",
                subtopic.id,
                exc_info=True,
                extra={"course_blocks_available": bool(course_blocks)},
            )
            raise

    @staticmethod
    def _extract_lti_consumer_id(
        course_blocks: Dict[str, Any]
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Locates and extracts the first LTI consumer block ID from course structure.

        Args:
            course_blocks: Course blocks data with root and blocks information

        Returns:
            First LTI consumer block ID if found, None otherwise
        """
        blocks = course_blocks.get("blocks", {})
        print(blocks, "here are the blocks")

        for block_id, block_data in blocks.items():
            if block_data.get("type") == "lti_consumer":
                logger.info("Found LTI consumer block: %s", block_id)
                return block_id, block_data.get("display_name")

        logger.warning("No LTI consumer block found in course blocks")
        return None, None
