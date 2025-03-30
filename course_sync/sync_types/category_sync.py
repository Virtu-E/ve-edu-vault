from typing import Dict, Set

from django.db.models.signals import post_delete

from course_sync.data_transformer import StructureExtractor
from course_sync.sync_types.abstract_type import DatabaseSync
from course_ware.models import AcademicClass, Category, Course, ExaminationLevel, Topic


class CategorySync(DatabaseSync):
    """Responsible for synchronizing categories"""

    def __init__(
        self,
        course: Course,
        academic_class: AcademicClass,
        examination_level: ExaminationLevel,
        extractor: StructureExtractor,
    ):
        self.course = course
        self.academic_class = academic_class
        self.examination_level = examination_level
        self._extractor = extractor

    def sync(self, structure: Dict) -> None:
        categories = self._extractor.extract(structure).categories
        existing_categories = set(
            Category.objects.filter(course=self.course).values_list(
                "block_id", flat=True
            )
        )

        self._delete_removed_categories(existing_categories - categories)
        self._update_categories(structure)

    def _delete_removed_categories(self, removed_categories: Set[str]) -> None:
        topics_qs = Topic.objects.filter(
            category__course=self.course, category__block_id__in=removed_categories
        )
        categories_qs = Category.objects.filter(
            course=self.course, block_id__in=removed_categories
        )

        # Load objects into lists so we can send post_delete signals later.
        topics_to_delete = list(topics_qs)
        categories_to_delete = list(categories_qs)

        topics_qs.delete()
        categories_qs.delete()

        # Manually trigger post_delete signals for each deleted instance.
        for topic in topics_to_delete:
            post_delete.send(sender=Topic, instance=topic)
        for category in categories_to_delete:
            post_delete.send(sender=Category, instance=category)

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
