import logging
from typing import Dict, Optional

from django.db import transaction

from course_sync.comparator import StructureComparator
from course_sync.side_effects import TopicCreationSideEffect
from course_sync.sync_types import CategorySync, TopicSync
from course_ware.models import AcademicClass, Course, ExaminationLevel
from exceptions import DatabaseUpdateError
from no_sql_database.mongodb import mongo_database

log = logging.getLogger(__name__)


# TODO : call this function inside of a celery task
class CourseSync:
    """Orchestrates the synchronization of course structure from edx"""

    def __init__(
        self,
        course: Course,
        academic_class: AcademicClass,
        examination_level: ExaminationLevel,
        new_structure: Optional[Dict] = None,
    ):
        self.course = course
        self.stored_structure = course.course_outline
        self.new_structure = new_structure
        self.comparator = StructureComparator()
        # TODO : We should use dependency injection here
        self.category_sync = CategorySync(course, academic_class, examination_level)
        self.topic_sync = TopicSync(course, TopicCreationSideEffect(mongo_database))

    @transaction.atomic
    def sync(self, force: bool = False) -> bool:
        """
        Synchronize the course structure with the database.
        Args:
            force: If True, sync will proceed even if no changes detected
        Returns:
            bool: True if sync was performed, False if no changes detected
        """
        if not force and self.new_structure:
            if not self.comparator.has_changes(
                self.stored_structure, self.new_structure
            ):
                log.info(f"No changes detected for course {self.course.name}")
                return False

            self._update_course_name()
            self._update_stored_structure()

        structure_to_sync = (
            self.new_structure if self.new_structure else self.stored_structure
        )

        try:
            self.category_sync.sync(structure_to_sync)
            self.topic_sync.sync(structure_to_sync)
            return True
        except Exception as e:
            log.error(f"Error syncing course structure: {e}")
            raise DatabaseUpdateError(f"Error syncing course structure: {e}")

    def _update_course_name(self) -> None:
        new_name = self.new_structure.get("course_structure", {}).get("display_name")
        if new_name and new_name != self.course.name:
            self.course.name = new_name
            self.course.save()

    def _update_stored_structure(self) -> None:
        self.course.course_outline = self.new_structure
        self.course.save()
