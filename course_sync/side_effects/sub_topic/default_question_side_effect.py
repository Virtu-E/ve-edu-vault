import logging
from typing import Dict, List

from course_ware.models import DefaultQuestionSet, SubTopic

logger = logging.getLogger(__name__)


class DefaultQuestionSetAssignerMixin:
    """
    Mixin class that ensures each new subtopic has an assigned default question set.
    """

    def sync_question_set(
        self, questions: List[Dict[str, str]], subtopic: SubTopic
    ) -> None:
        """
        Synchronizes the default question set for a subtopic.

        Args:
            questions: List of question dictionaries
            subtopic: The subtopic to associate with the question set
        """
        logger.info(
            "Synchronizing question set for subtopic %s with %d questions",
            subtopic.name,
            len(questions),
        )
        try:
            DefaultQuestionSet.objects.update_or_create(
                sub_topic=subtopic, defaults={"question_list_ids": questions}
            )
        except SubTopic.DoesNotExist:
            logger.error(
                "Failed to sync question set for subtopic %s",
                subtopic.id,
                exc_info=True,
                extra={"question_count": len(questions)},
            )
            raise
