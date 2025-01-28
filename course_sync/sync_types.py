import logging
from abc import ABC, abstractmethod
from typing import Dict, Set

from course_sync.extractor import StructureExtractor
from course_sync.side_effects import CreationSideEffect
from course_ware.models import AcademicClass, Category, Course, Topic

log = logging.getLogger(__name__)


class DatabaseSync(ABC):
    """Abstract base class for database synchronization"""

    @abstractmethod
    def sync(self, structure: Dict) -> None:
        pass


class CategorySync(DatabaseSync):
    """Responsible for synchronizing categories"""

    def __init__(
        self, course: Course, academic_class: AcademicClass, examination_level: str
    ):
        self.course = course
        self.academic_class = academic_class
        self.examination_level = examination_level

    def sync(self, structure: Dict) -> None:
        categories = StructureExtractor.extract(structure).categories
        existing_categories = set(
            Category.objects.filter(course=self.course).values_list(
                "block_id", flat=True
            )
        )

        self._delete_removed_categories(existing_categories - categories)
        self._update_categories(structure)

    def _delete_removed_categories(self, removed_categories: Set[str]) -> None:
        Category.objects.filter(
            course=self.course, block_id__in=removed_categories
        ).delete()

    def _update_categories(self, structure: Dict) -> None:
        chapters = StructureExtractor.extract_chapters(structure)
        for chapter in chapters:
            Category.objects.update_or_create(
                block_id=chapter.id,
                course=self.course,
                academic_class=self.academic_class,
                defaults={
                    "name": chapter.name,
                    "examination_level": self.examination_level,
                },
            )


class TopicSync(DatabaseSync):
    """Responsible for synchronizing topics"""

    def __init__(self, course: Course, creation_side_effect: CreationSideEffect):
        self.course = course
        self.creation_side_effect = creation_side_effect

    def sync(self, structure: Dict) -> None:
        structure_data = StructureExtractor.extract(structure)
        existing_topics = set(
            Topic.objects.filter(category__course=self.course).values_list(
                "block_id", flat=True
            )
        )

        self._delete_removed_topics(existing_topics - structure_data.topics)
        self._update_topics(structure)

    def _delete_removed_topics(self, removed_topics: Set[str]) -> None:
        Topic.objects.filter(
            category__course=self.course, block_id__in=removed_topics
        ).delete()

    def _update_topics(self, structure: Dict) -> None:
        chapters = StructureExtractor.extract_chapters(structure)
        for chapter in chapters:
            try:
                category = Category.objects.get(course=self.course, block_id=chapter.id)
                objectives = StructureExtractor.extract_objectives(chapter)

                for objective in objectives:
                    topic_instance, created = Topic.objects.update_or_create(
                        block_id=objective.id,
                        defaults={
                            "name": objective.name,
                            "category": category,
                        },
                    )
                    self.creation_side_effect.process_creation_side_effects(
                        topic_instance
                    )

            except Category.DoesNotExist:
                log.error(f"Category not found for chapter {chapter.id}")
                continue
