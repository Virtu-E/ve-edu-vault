import copy
from unittest.mock import patch

import pytest

from course_ware.course_sync import CourseSync
from course_ware.models import Category, Topic
from exceptions import DatabaseQueryError, DatabaseUpdateError


@pytest.mark.django_db
class TestCourseSync:

    def test_get_existing_ids_empty_db(self, course_sync):
        """Test getting IDs when database is empty"""
        categories, topics = course_sync._get_existing_ids()
        assert categories == set()
        assert topics == set()

    def test_get_existing_ids_with_data(self, course_sync, category, topic):
        """Test getting IDs with existing data in database"""
        categories, topics = course_sync._get_existing_ids()
        assert categories == {category.block_id}
        assert topics == {topic.block_id}

    @patch("course_ware.models.Category.objects")
    def test_get_existing_ids_database_error(self, mock_category_objects, course_sync):
        """Test database error handling in get_existing_ids"""
        mock_category_objects.filter.side_effect = Exception("Database error")

        with pytest.raises(DatabaseQueryError) as exc_info:
            course_sync._get_existing_ids()

        assert "Error getting course related categories and topics" in str(
            exc_info.value
        )

    def test_get_outline_ids(self, course_sync):
        """Test extracting IDs from outline data"""
        outline = {
            "chapter1": {"type": "chapter"},
            "sequential1": {"type": "sequential"},
        }
        categories, topics = course_sync._get_outline_ids(outline)
        assert categories == {"chapter1"}
        assert topics == {"sequential1"}

    def test_has_changes_no_new_outline(self, course_sync):
        """Test change detection when no new outline provided"""
        assert not course_sync._has_changes()

    def test_has_changes_structural_difference(self, course, academic_class):
        """Test change detection with structural differences"""
        new_outline = {
            "chapter1": {"type": "chapter", "display_name": "Chapter 1", "children": []}
        }
        sync = CourseSync(course, academic_class, new_outline)
        assert sync._has_changes()

    def test_has_changes_content_difference(self, course, academic_class):
        """Test change detection with content differences"""
        new_outline = copy.deepcopy(course.course_outline)
        new_outline["chapter1"]["display_name"] = "Updated Chapter 1"
        sync = CourseSync(course, academic_class, new_outline)
        assert sync._has_changes()

    @patch("logging.getLogger")
    def test_sync_categories_create(self, mock_logger, course_sync):
        """Test category creation during sync"""
        existing = set()
        outline = {"chapter1"}
        outline_data = {
            "chapter1": {
                "type": "chapter",
                "display_name": "New Chapter",
                "description": "Description",
            }
        }
        course_sync._sync_categories(existing, outline, outline_data)
        assert Category.objects.count() == 1
        category = Category.objects.first()
        assert category.name == "New Chapter"
        assert category.block_id == "chapter1"

    @patch("course_ware.models.Category.objects")
    def test_sync_categories_database_error(self, mock_category_objects, course_sync):
        """Test database error handling in sync_categories"""
        mock_category_objects.filter.side_effect = Exception("Database error")

        with pytest.raises(DatabaseUpdateError) as exc_info:
            course_sync._sync_categories(set(), {"chapter1"}, {})

        assert "Error syncing categories" in str(exc_info.value)

    def test_sync_topics_create(self, course_sync, category):
        """Test topic creation during sync"""
        existing = set()
        outline = {"sequential1"}
        outline_data = {
            f"{category.block_id}": {"type": "chapter", "children": ["sequential1"]},
            "sequential1": {
                "type": "sequential",
                "display_name": "New Topic",
                "description": "Description",
            },
        }
        course_sync._sync_topics(existing, outline, outline_data)
        assert Topic.objects.count() == 1
        topic = Topic.objects.first()
        assert topic.name == "New Topic"
        assert topic.block_id == "sequential1"

    @patch("course_ware.models.Topic.objects")
    def test_sync_topics_database_error(self, mock_topic_objects, course_sync):
        """Test database error handling in sync_topics"""
        mock_topic_objects.filter.side_effect = Exception("Database error")

        with pytest.raises(DatabaseUpdateError) as exc_info:
            course_sync._sync_topics(set(), {"sequential1"}, {})

        assert "Error syncing topics" in str(exc_info.value)

    def test_sync_force_update(self, course, academic_class):
        """Test forced sync operation"""
        new_outline = {
            "chapter2": {
                "type": "chapter",
                "display_name": "New Chapter",
                "children": ["sequential2"],
            },
            "sequential2": {
                "type": "sequential",
                "display_name": "New Sequential",
                "children": [],
            },
        }
        sync = CourseSync(course, academic_class, new_outline)
        result = sync.sync(force=True)
        assert result is True
        assert Category.objects.count() == 1
        assert Topic.objects.count() == 1

    def test_sync_no_changes(self, course, academic_class):
        """Test sync operation when no changes detected"""
        sync = CourseSync(course, academic_class, course.course_outline)
        result = sync.sync()
        assert result is False

    def test_sync_updates_course_outline(self, course, academic_class):
        """Test that sync updates course outline when changes detected"""
        new_outline = {
            "chapter1": {
                "type": "chapter",
                "display_name": "Updated Chapter",
                "children": ["sequential1"],
            },
            "sequential1": {
                "type": "sequential",
                "display_name": "Updated Sequential",
                "children": [],
            },
        }
        sync = CourseSync(course, academic_class, new_outline)
        sync.sync()
        course.refresh_from_db()
        assert course.course_outline == new_outline
