import logging
from typing import Dict, Set

from django.db.models.signals import post_delete

from course_sync.data_transformer import StructureExtractor
from course_sync.sync_types.abstract_type import DatabaseSync
from course_ware.models import Category, Course, Topic

log = logging.getLogger(__name__)


class TopicSync(DatabaseSync):
    """Responsible for synchronizing topics into database"""

    def __init__(self, course: Course, extractor: StructureExtractor):
        self.course = course
        self._extractor = extractor

    def sync(self, structure: Dict) -> None:
        structure_data = self._extractor.extract(structure)
        existing_topics = set(
            Topic.objects.filter(category__course=self.course).values_list(
                "block_id", flat=True
            )
        )

        self._delete_removed_topics(existing_topics - structure_data.topics)
        self._update_topics(structure)

    def _delete_removed_topics(self, removed_topics: Set[str]) -> None:
        topics_qs = Topic.objects.filter(
            category__course=self.course, block_id__in=removed_topics
        )
        topics_to_delete = list(topics_qs)
        topics_qs.delete()

        # sending delete signal here since bulk deletion does not send that
        for topic in topics_to_delete:
            post_delete.send(sender=Topic, instance=topic)

    def _update_topics(self, structure: Dict) -> None:
        chapters = StructureExtractor.extract_chapters(structure)
        for chapter in chapters:
            try:
                category = Category.objects.get(course=self.course, block_id=chapter.id)
                objectives = StructureExtractor.extract_objectives(chapter)

                for objective in objectives:
                    Topic.objects.update_or_create(
                        block_id=objective.id,
                        defaults={
                            "name": objective.name,
                            "category": category,
                        },
                    )

            except Category.DoesNotExist:
                log.error(f"Category not found for chapter {chapter.id}")
                continue
