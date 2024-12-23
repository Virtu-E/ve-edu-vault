import logging
from typing import Dict, Set

from django.db import transaction

from course_ware.models import AcademicClass, Category, Course, Topic
from data_types.course_ware_schema import Block
from exceptions import DatabaseQueryError, DatabaseUpdateError

log = logging.getLogger(__name__)


class CourseSync:
    """
    Responsible for synchronizing edx course outline with edu vault.
    """

    def __init__(
        self,
        course: Course,
        academic_class: AcademicClass,
        new_outline: Dict[str, Block] = None,
    ):
        """
        Initialize the CourseSync class.

        Args:
            course: Course model instance
            academic_class: AcademicClass model instance
            new_outline: Optional fresh course outline from API
        """
        self.course = course
        self.category_model = Category
        self.topic_model = Topic
        self.academic_class = academic_class
        self.stored_outline = course.course_outline
        self.new_outline = new_outline

    def _get_existing_ids(self) -> tuple[Set[str], Set[str]]:
        """Get existing category and topic IDs from the database."""
        try:
            existing_categories = set(
                self.category_model.objects.filter(course=self.course).values_list(
                    "block_id", flat=True
                )
            )
            existing_topics = set(
                self.topic_model.objects.filter(
                    category__course=self.course
                ).values_list("block_id", flat=True)
            )
            return existing_categories, existing_topics

        except Exception as e:
            log.error(
                f"Error getting existing categories and topics for course {self.course.name}: {e}"
            )
            raise DatabaseQueryError(
                f"Error getting course related categories and topics for course {self.course.name}: {e}"
            )

    @staticmethod
    def _get_outline_ids(outline_data: Dict[str, Block]) -> tuple[Set[str], Set[str]]:
        """
        Extract category and topic IDs from the provided outline.

        Args:
            outline_data: Course outline dictionary

        Returns:
            Tuple of sets containing category and topic IDs
        """
        outline_categories = set()
        outline_topics = set()

        for block_id, block_data in outline_data.items():
            if block_data["type"] == "chapter":
                outline_categories.add(block_id)
            elif block_data["type"] == "sequential":
                outline_topics.add(block_id)

        return outline_categories, outline_topics

    def _has_changes(self) -> bool:
        """
        Check if there are differences between stored and new outline.
        Only relevant when new_outline is provided.
        """
        if not self.new_outline:
            return False

        stored_categories, stored_topics = self._get_outline_ids(self.stored_outline)
        new_categories, new_topics = self._get_outline_ids(self.new_outline)

        # Check for structural changes (additions/deletions)
        if stored_categories != new_categories or stored_topics != new_topics:
            return True

        # Check for content changes in existing blocks
        all_blocks = stored_categories.union(stored_topics)
        for block_id in all_blocks:
            if block_id not in self.new_outline:
                continue

            stored_block = self.stored_outline.get(block_id, {})
            new_block = self.new_outline.get(block_id, {})

            # Compare relevant fields
            fields_to_compare = ["display_name", "description", "children"]
            for field in fields_to_compare:
                if stored_block.get(field) != new_block.get(field):
                    return True

        return False

    def _sync_categories(
        self,
        existing_categories: Set[str],
        outline_categories: Set[str],
        outline_data: Dict,
    ):
        """
        Sync categories (chapters) with the database.

        Args:
            existing_categories: Set of existing category IDs in database
            outline_categories: Set of category IDs from outline
            outline_data: Course outline dictionary to sync from
        """
        try:
            # Delete categories that are no longer in the outline
            categories_to_delete = existing_categories - outline_categories
            self.category_model.objects.filter(
                course=self.course, block_id__in=categories_to_delete
            ).delete()

            # Update or create categories from the outline
            for block_id in outline_categories:
                block_data = outline_data[block_id]
                category_data = {
                    "name": block_data["display_name"],
                    "block_id": block_id,
                    "course": self.course,
                    "description": block_data.get("description", ""),
                }

                self.category_model.objects.update_or_create(
                    block_id=block_id,
                    course=self.course,
                    academic_class=self.academic_class,
                    defaults=category_data,
                )
        except Exception as e:
            log.error(f"Error syncing categories for course {self.course.name}: {e}")
            raise DatabaseUpdateError(
                f"Error syncing categories course {self.course.name}: {e}"
            )

    def _sync_topics(
        self, existing_topics: Set[str], outline_topics: Set[str], outline_data: Dict
    ):
        """
        Sync topics (sequential) with the database.

        Args:
            existing_topics: Set of existing topic IDs in database
            outline_topics: Set of topic IDs from outline
            outline_data: Course outline dictionary to sync from
        """
        try:
            # Delete topics that are no longer in the outline
            topics_to_delete = existing_topics - outline_topics
            self.topic_model.objects.filter(
                category__course=self.course, block_id__in=topics_to_delete
            ).delete()

            # Update or create topics from the outline
            for block_id in outline_topics:
                block_data = outline_data[block_id]

                # Find the parent category
                parent_id = None
                for category_id, category_data in outline_data.items():
                    if category_data[
                        "type"
                    ] == "chapter" and block_id in category_data.get("children", []):
                        parent_id = category_id
                        break

                if parent_id:
                    category = self.category_model.objects.get(
                        course=self.course, block_id=parent_id
                    )

                    topic_data = {
                        "name": block_data["display_name"],
                        "block_id": block_id,
                        "category": category,
                        "description": block_data.get("description", ""),
                    }

                    self.topic_model.objects.update_or_create(
                        block_id=block_id,
                        category__course=self.course,
                        defaults=topic_data,
                    )
        except Exception as e:
            log.error(f"Error syncing topics for course {self.course.name}: {e}")
            raise DatabaseUpdateError(
                f"Error syncing topics for course {self.course.name}: {e}"
            )

    @transaction.atomic
    def sync(self, force: bool = False) -> bool:
        """
        Synchronize the course outline with the database.

        Args:
            force: If True, sync will proceed even if no changes detected

        Returns:
            bool: True if sync was performed, False if no changes detected
        """
        # If new outline is provided, check for changes
        if self.new_outline and not force:
            if not self._has_changes():
                log.info(f"No changes detected for course {self.course.name}")
                return False
            # Update stored outline if there are changes
            self.course.course_outline = self.new_outline
            self.course.save()

        log.info(f"Syncing course {self.course.name}...")
        # Use new outline if provided, otherwise use stored outline
        outline_to_sync = self.new_outline if self.new_outline else self.stored_outline

        # Get existing IDs from database
        existing_categories, existing_topics = self._get_existing_ids()

        # Get IDs from outline to sync
        outline_categories, outline_topics = self._get_outline_ids(outline_to_sync)

        # Sync categories first (since topics depend on categories)
        self._sync_categories(existing_categories, outline_categories, outline_to_sync)

        # Then sync topics
        self._sync_topics(existing_topics, outline_topics, outline_to_sync)

        return True
