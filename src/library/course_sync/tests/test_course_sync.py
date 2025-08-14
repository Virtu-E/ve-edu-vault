from unittest.mock import MagicMock, patch

import pytest

from src.apps.core.courses.tests.factories import (AcademicClassFactory,
                                                   CourseFactory,
                                                   ExaminationLevelFactory)

from ..course_sync import ChangeResult, CourseSyncService
from ..data_transformer import EdxDataTransformer
from ..data_types import (ChangeOperation, CourseChangeData, CourseStructure,
                          EdxCourseOutline, EntityType, OperationType)
from ..diff_engine import DiffEngine


@pytest.fixture
def mock_diff_engine():
    """Create a mock DiffEngine."""
    return MagicMock(spec=DiffEngine)


@pytest.fixture
def course_sync_service(mock_diff_engine):
    """Create a CourseSyncService with a mock DiffEngine."""
    return CourseSyncService(diff_engine=mock_diff_engine)


@pytest.fixture
def course():
    """Create a test course."""
    return CourseFactory(course_key="test-course-id", name="Test Course")


@pytest.fixture
def examination_level():
    """Create a test examination level."""
    return ExaminationLevelFactory()


@pytest.fixture
def academic_class():
    """Create a test academic class."""
    return AcademicClassFactory()


@pytest.fixture
def mock_course_outline():
    """Create a mock course outline."""
    outline = MagicMock(spec=EdxCourseOutline)
    outline.course_id = "test-course-id"
    outline.title = "Test Course"
    outline.structure = MagicMock(spec=CourseStructure)
    outline.structure.topics = {"topic-1", "topic-2"}
    outline.topics = []
    return outline


@pytest.fixture
def mock_old_course_outline():
    """Create a mock for the old course outline created from the course model data."""
    outline = MagicMock(spec=EdxCourseOutline)
    outline.course_id = "test-course-id"
    outline.title = "Test Course"
    return outline


class TestCourseSyncService:
    """Tests for the CourseSyncService."""

    @patch.object(EdxDataTransformer, "transform_to_course_outline")
    def test_sync_course_no_changes(
        self,
        mock_transform,
        course_sync_service,
        mock_diff_engine,
        course,
        examination_level,
        academic_class,
        mock_course_outline,
        mock_old_course_outline,
    ):
        """Test sync_course when there are no changes detected."""
        # Arrange
        mock_transform.return_value = mock_old_course_outline
        mock_diff_engine.diff.return_value = []

        # Act
        result = course_sync_service.sync_course(
            mock_course_outline, course, examination_level, academic_class
        )

        # Assert
        assert isinstance(result, ChangeResult)
        assert result.num_success == 0
        assert result.num_failed == 0

        mock_transform.assert_called_once_with(
            structure=course.course_outline,
            course_id=course.course_key,
            title=course.name,
        )
        mock_diff_engine.diff.assert_called_once_with(
            mock_old_course_outline, mock_course_outline
        )

    @patch.object(EdxDataTransformer, "transform_to_course_outline")
    def test_sync_course_with_successful_changes(
        self,
        mock_transform,
        course_sync_service,
        mock_diff_engine,
        course,
        examination_level,
        academic_class,
        mock_course_outline,
        mock_old_course_outline,
    ):
        """Test sync_course when there are changes that are successfully processed."""
        # Arrange
        mock_transform.return_value = mock_old_course_outline

        changes = [
            ChangeOperation(
                operation=OperationType.UPDATE,
                entity_type=EntityType.COURSE,
                entity_id="test-course-id",
                data=CourseChangeData(name="Updated Course", course_outline={}),
            )
        ]
        mock_diff_engine.diff.return_value = changes

        # Act
        with patch(
            "src.library.course_sync.course_sync.ChangeProcessor"
        ) as mock_processor_class:
            mock_processor = mock_processor_class.return_value
            mock_processor.process_changes.return_value = []  # No failed changes

            result = course_sync_service.sync_course(
                mock_course_outline, course, examination_level, academic_class
            )

            # Assert
            assert isinstance(result, ChangeResult)
            assert result.num_success == 1
            assert result.num_failed == 0

            mock_transform.assert_called_once_with(
                structure=course.course_outline,
                course_id=course.course_key,
                title=course.name,
            )
            mock_diff_engine.diff.assert_called_once_with(
                mock_old_course_outline, mock_course_outline
            )
            mock_processor_class.assert_called_once_with(
                course=course,
                examination_level=examination_level,
                academic_class=academic_class,
            )
            mock_processor.process_changes.assert_called_once_with(changes)

    @patch.object(EdxDataTransformer, "transform_to_course_outline")
    def test_sync_course_with_failed_changes(
        self,
        mock_transform,
        course_sync_service,
        mock_diff_engine,
        course,
        examination_level,
        academic_class,
        mock_course_outline,
        mock_old_course_outline,
    ):
        """Test sync_course when there are changes that fail to process."""
        # Arrange
        mock_transform.return_value = mock_old_course_outline

        changes = [
            ChangeOperation(
                operation=OperationType.UPDATE,
                entity_type=EntityType.COURSE,
                entity_id="test-course-id",
                data=CourseChangeData(name="Updated Course", course_outline={}),
            ),
            ChangeOperation(
                operation=OperationType.CREATE,
                entity_type=EntityType.TOPIC,
                entity_id="topic-1",
                data=MagicMock(),
            ),
        ]
        mock_diff_engine.diff.return_value = changes

        # Act
        with patch(
            "src.library.course_sync.course_sync.ChangeProcessor"
        ) as mock_processor_class:
            mock_processor = mock_processor_class.return_value
            # The second change failed
            mock_processor.process_changes.return_value = [changes[1]]

            result = course_sync_service.sync_course(
                mock_course_outline, course, examination_level, academic_class
            )

            # Assert
            assert isinstance(result, ChangeResult)
            assert result.num_success == 1
            assert result.num_failed == 1

            mock_transform.assert_called_once_with(
                structure=course.course_outline,
                course_id=course.course_key,
                title=course.name,
            )
            mock_diff_engine.diff.assert_called_once_with(
                mock_old_course_outline, mock_course_outline
            )
            mock_processor_class.assert_called_once_with(
                course=course,
                examination_level=examination_level,
                academic_class=academic_class,
            )
            mock_processor.process_changes.assert_called_once_with(changes)

    @patch.object(EdxDataTransformer, "transform_to_course_outline")
    def test_sync_course_with_partially_successful_changes(
        self,
        mock_transform,
        course_sync_service,
        mock_diff_engine,
        course,
        examination_level,
        academic_class,
        mock_course_outline,
        mock_old_course_outline,
    ):
        """Test sync_course when there are multiple changes with mixed success."""
        # Arrange
        mock_transform.return_value = mock_old_course_outline

        changes = [
            ChangeOperation(
                operation=OperationType.UPDATE,
                entity_type=EntityType.COURSE,
                entity_id="test-course-id",
                data=CourseChangeData(name="Updated Course", course_outline={}),
            ),
            ChangeOperation(
                operation=OperationType.CREATE,
                entity_type=EntityType.TOPIC,
                entity_id="topic-1",
                data=MagicMock(),
            ),
            ChangeOperation(
                operation=OperationType.DELETE,
                entity_type=EntityType.SUBTOPIC,
                entity_id="subtopic-1",
                data=None,
            ),
        ]
        mock_diff_engine.diff.return_value = changes

        # Act
        with patch(
            "src.library.course_sync.course_sync.ChangeProcessor"
        ) as mock_processor_class:
            mock_processor = mock_processor_class.return_value
            # Two changes failed
            mock_processor.process_changes.return_value = [changes[1], changes[2]]

            result = course_sync_service.sync_course(
                mock_course_outline, course, examination_level, academic_class
            )

            # Assert
            assert isinstance(result, ChangeResult)
            assert result.num_success == 1
            assert result.num_failed == 2

            mock_transform.assert_called_once_with(
                structure=course.course_outline,
                course_id=course.course_key,
                title=course.name,
            )
            mock_diff_engine.diff.assert_called_once_with(
                mock_old_course_outline, mock_course_outline
            )
            mock_processor_class.assert_called_once_with(
                course=course,
                examination_level=examination_level,
                academic_class=academic_class,
            )
            mock_processor.process_changes.assert_called_once_with(changes)

    @patch("logging.Logger.info")
    def test_detect_changes_method(
        self, mock_log, course_sync_service, mock_diff_engine, mock_course_outline
    ):
        """Test the _detect_changes method directly."""
        # Arrange
        old_outline = MagicMock(spec=EdxCourseOutline)
        old_outline.course_id = "test-course-id"
        mock_diff_engine.diff.return_value = []

        # Act
        result = course_sync_service._detect_changes(old_outline, mock_course_outline)

        # Assert
        assert result == []
        mock_diff_engine.diff.assert_called_once_with(old_outline, mock_course_outline)
        mock_log.assert_called_with(
            "Detecting changes for course ID: %s", mock_course_outline.course_id
        )

    @patch("logging.Logger.info")
    def test_process_changes_method(
        self, mock_log, course_sync_service, course, examination_level, academic_class
    ):
        """Test the _process_changes method directly."""
        # Arrange
        changes = [
            ChangeOperation(
                operation=OperationType.UPDATE,
                entity_type=EntityType.COURSE,
                entity_id="test-course-id",
                data=MagicMock(),
            )
        ]

        # Act
        with patch(
            "src.library.course_sync.course_sync.ChangeProcessor"
        ) as mock_processor_class:
            mock_processor = mock_processor_class.return_value
            mock_processor.process_changes.return_value = []

            result = course_sync_service._process_changes(
                changes, course, examination_level, academic_class
            )

            # Assert
            assert result == []
            mock_processor_class.assert_called_once_with(
                course=course,
                examination_level=examination_level,
                academic_class=academic_class,
            )
            mock_processor.process_changes.assert_called_once_with(changes)
            mock_log.assert_called_with(
                "Processing %d changes for course ID: %s", len(changes), course.id
            )

    @patch.object(DiffEngine, "__init__", return_value=None)
    def test_create_service_method(self, mock_diff_init):
        """Test the create_service classmethod."""
        # Act
        with patch.object(
            DiffEngine, "diff"
        ):  # Mock the diff method to avoid implementation details
            service = CourseSyncService.create_service()

            # Assert
            assert isinstance(service, CourseSyncService)
            mock_diff_init.assert_called_once()
