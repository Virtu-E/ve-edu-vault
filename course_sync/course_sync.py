import logging
from typing import Dict, Optional

from django.db import transaction
from typing_extensions import Type

from course_sync.comparator import StructureComparator
from course_sync.extractor import StructureExtractor
from course_sync.sync_types.abstract_type import DatabaseSync
from course_sync.sync_types.category_sync import CategorySync
from course_sync.sync_types.topic_sync import TopicSync
from course_ware.models import AcademicClass, Course, ExaminationLevel
from exceptions import DatabaseUpdateError

log = logging.getLogger(__name__)


class CourseSync:
    """Orchestrates the synchronization of course structure from edx"""

    def __init__(
        self,
        course: Course,
        topic_sync: DatabaseSync,
        category_sync: DatabaseSync,
        comparator: StructureComparator,
        new_structure: Optional[Dict] = None,
    ):
        self._course = course
        self._stored_structure = course.course_outline
        self._new_structure = new_structure
        self._comparator = comparator
        self._category_sync = category_sync
        self._topic_sync = topic_sync

    @transaction.atomic
    def sync(self, force: bool = False) -> bool:
        """
        Synchronize the course structure with the database.
        Args:
            force: If True, sync will proceed even if no changes detected
        Returns:
            bool: True if sync was performed, False if no changes detected
        """
        if not force and self._new_structure:
            if not self._comparator.has_changes(
                self._stored_structure, self._new_structure
            ):
                log.info(f"No changes detected for course {self._course.name}")
                return False

            self._update_course_name()
            self._update_stored_structure()

        structure_to_sync = (
            self._new_structure if self._new_structure else self._stored_structure
        )

        try:
            self._category_sync.sync(structure_to_sync)
            self._topic_sync.sync(structure_to_sync)
            return True
        except Exception as e:
            log.error(f"Error syncing course structure: {e}")
            raise DatabaseUpdateError(f"Error syncing course structure: {e}")

    def _update_course_name(self) -> None:
        new_name = self._new_structure.get("course_structure", {}).get("display_name")
        if new_name and new_name != self._course.name:
            self._course.name = new_name
            self._course.save()

    def _update_stored_structure(self) -> None:
        self._course.course_outline = self._new_structure
        self._course.save()


class CourseSyncFactory:
    @staticmethod
    def create(
        course: Course,
        academic_class: AcademicClass,
        examination_level: ExaminationLevel,
        extractor: Type[StructureExtractor],
        new_structure: Optional[Dict] = None,
    ) -> CourseSync:
        extractor_instance = extractor()
        comparator = StructureComparator()
        category_sync = CategorySync(
            course, academic_class, examination_level, extractor_instance
        )
        topic_sync = TopicSync(course, extractor_instance)

        return CourseSync(
            course=course,
            comparator=comparator,
            category_sync=category_sync,
            topic_sync=topic_sync,
            new_structure=new_structure,
        )
