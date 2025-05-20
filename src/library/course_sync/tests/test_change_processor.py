from unittest.mock import MagicMock, patch

from src.apps.core.content.models import SubTopic, Topic
from src.apps.core.courses.models import Course

from ..data_types import (
    ChangeOperation,
    CourseChangeData,
    DefaultChangeData,
    EntityType,
    OperationType,
    SubTopicChangeData,
)


class TestCreateStrategy:
    """Tests for the CreateStrategy implementation."""

    def test_topic_creation_succeeds(self, create_strategy):
        """Test that a Topic can be successfully created."""
        # Arrange
        topic_id = "topic-123"
        topic_data = DefaultChangeData(name="Test Topic")
        change = ChangeOperation(
            operation=OperationType.CREATE,
            entity_type=EntityType.TOPIC,
            entity_id=topic_id,
            data=topic_data,
        )
        topics_count_before = Topic.objects.count()

        # Act
        result = create_strategy.process(change)

        # Assert
        assert result is True
        assert Topic.objects.count() == topics_count_before + 1

        created_topic = Topic.objects.get(block_id=topic_id)
        assert created_topic.name == topic_data.name
        assert created_topic.examination_level == create_strategy._examination_level
        assert created_topic.academic_class == create_strategy._academic_class
        assert created_topic.course == create_strategy._course

    def test_subtopic_creation_succeeds(self, create_strategy, topic):
        """Test that a SubTopic can be successfully created."""
        # Arrange
        subtopic_id = "subtopic-456"
        subtopic_data = SubTopicChangeData(
            name="Test SubTopic", topic_id=topic.block_id
        )
        change = ChangeOperation(
            operation=OperationType.CREATE,
            entity_type=EntityType.SUBTOPIC,
            entity_id=subtopic_id,
            data=subtopic_data,
        )
        subtopics_count_before = SubTopic.objects.count()

        # Act
        result = create_strategy.process(change)

        # Assert
        assert result is True
        assert SubTopic.objects.count() == subtopics_count_before + 1

        created_subtopic = SubTopic.objects.get(block_id=subtopic_id)
        assert created_subtopic.name == subtopic_data.name
        assert created_subtopic.topic.block_id == subtopic_data.topic_id

    def test_unsupported_entity_creation_fails(self, create_strategy):
        """Test that creating an unsupported entity type returns False."""
        # Arrange
        course_id = "course-789"
        course_data = CourseChangeData(name="Test Course", course_outline={})
        change = ChangeOperation(
            operation=OperationType.CREATE,
            entity_type=EntityType.COURSE,  # Unsupported for creation
            entity_id=course_id,
            data=course_data,
        )

        # Act
        result = create_strategy.process(change)

        # Assert
        assert result is False


class TestUpdateStrategy:
    """Tests for the UpdateStrategy implementation."""

    def test_course_update_succeeds(self, update_strategy, course):
        """Test that a Course can be successfully updated."""
        # Arrange
        updated_name = "Updated Course"
        updated_outline = {"hello": "world"}

        course_data = CourseChangeData(
            name=updated_name, course_outline=updated_outline
        )

        change = ChangeOperation(
            operation=OperationType.UPDATE,
            entity_type=EntityType.COURSE,
            entity_id=course.id,
            data=course_data,
        )

        # Act
        result = update_strategy.process(change)

        # Assert
        assert result is True
        updated_course = Course.objects.get(id=course.id)
        assert updated_course.name == updated_name
        assert updated_course.course_outline == updated_outline

    def test_topic_update_succeeds(self, update_strategy, topic):
        """Test that a Topic can be successfully updated."""
        # Arrange
        updated_name = "Updated Topic"
        topic_data = DefaultChangeData(name=updated_name)

        change = ChangeOperation(
            operation=OperationType.UPDATE,
            entity_type=EntityType.TOPIC,
            entity_id=topic.block_id,
            data=topic_data,
        )

        # Act
        result = update_strategy.process(change)

        # Assert
        assert result is True
        updated_topic = Topic.objects.get(block_id=topic.block_id)
        assert updated_topic.name == updated_name

    def test_subtopic_update_succeeds(self, update_strategy, subtopic):
        """Test that a SubTopic can be successfully updated."""
        # Arrange
        updated_name = "Updated SubTopic"
        subtopic_data = SubTopicChangeData(
            name=updated_name, topic_id=subtopic.topic.block_id
        )

        change = ChangeOperation(
            operation=OperationType.UPDATE,
            entity_type=EntityType.SUBTOPIC,
            entity_id=subtopic.block_id,
            data=subtopic_data,
        )

        # Act
        result = update_strategy.process(change)

        # Assert
        assert result is True
        updated_subtopic = SubTopic.objects.get(block_id=subtopic.block_id)
        assert updated_subtopic.name == updated_name


class TestDeleteStrategy:
    """Tests for the DeleteStrategy implementation."""

    def test_course_deletion_succeeds(self, delete_strategy, course):
        """Test that a Course can be successfully deleted."""
        # Arrange
        change = ChangeOperation(
            operation=OperationType.DELETE,
            entity_type=EntityType.COURSE,
            entity_id=course.id,
            data=None,
        )

        # Act
        result = delete_strategy.process(change)

        # Assert
        assert result is True
        assert not Course.objects.filter(id=course.id).exists()

    def test_topic_deletion_succeeds(self, delete_strategy, topic):
        """Test that a Topic can be successfully deleted."""
        # Arrange
        change = ChangeOperation(
            operation=OperationType.DELETE,
            entity_type=EntityType.TOPIC,
            entity_id=topic.block_id,
            data=None,
        )

        # Act
        result = delete_strategy.process(change)

        # Assert
        assert result is True
        assert not Topic.objects.filter(block_id=topic.block_id).exists()

    def test_subtopic_deletion_succeeds(self, delete_strategy, subtopic):
        """Test that a SubTopic can be successfully deleted."""
        # Arrange
        change = ChangeOperation(
            operation=OperationType.DELETE,
            entity_type=EntityType.SUBTOPIC,
            entity_id=subtopic.block_id,
            data=None,
        )

        # Act
        result = delete_strategy.process(change)

        # Assert
        assert result is True
        assert not SubTopic.objects.filter(block_id=subtopic.block_id).exists()


class TestChangeProcessor:
    """Tests for the ChangeProcessor implementation."""

    def test_processor_initializes_with_correct_strategies(self, change_processor):
        """Test that the processor initializes with all required strategies."""
        # Assert
        assert len(change_processor._strategies) == 3
        assert OperationType.CREATE in change_processor._strategies
        assert OperationType.UPDATE in change_processor._strategies
        assert OperationType.DELETE in change_processor._strategies

    @patch("logging.Logger.error")
    def test_successful_processing_of_all_changes(self, mock_logger, change_processor):
        """Test that all changes are processed successfully."""
        # Arrange
        create_strategy_mock = MagicMock(return_value=True)
        update_strategy_mock = MagicMock(return_value=True)
        delete_strategy_mock = MagicMock(return_value=True)

        change_processor._strategies = {
            OperationType.CREATE: create_strategy_mock,
            OperationType.UPDATE: update_strategy_mock,
            OperationType.DELETE: delete_strategy_mock,
        }

        changes = [
            ChangeOperation(
                operation=OperationType.CREATE,
                entity_type=EntityType.TOPIC,
                entity_id="topic-123",
                data=MagicMock(),
            ),
            ChangeOperation(
                operation=OperationType.UPDATE,
                entity_type=EntityType.SUBTOPIC,
                entity_id="subtopic-456",
                data=MagicMock(),
            ),
            ChangeOperation(
                operation=OperationType.DELETE,
                entity_type=EntityType.COURSE,
                entity_id="course-789",
                data=None,
            ),
        ]

        # Act
        failed_changes = change_processor.process_changes(changes)

        # Assert
        assert len(failed_changes) == 0
        assert not mock_logger.called
        for strategy_mock in [
            create_strategy_mock,
            update_strategy_mock,
            delete_strategy_mock,
        ]:
            strategy_mock.process.assert_called_once()

    @patch("logging.Logger.error")
    def test_processing_with_failed_changes(self, mock_logger, change_processor):
        """Test that failed changes are properly reported."""
        # Arrange
        create_strategy_mock = MagicMock()
        create_strategy_mock.process.return_value = False  # This one fails

        change_processor._strategies = {
            OperationType.CREATE: create_strategy_mock,
        }

        failing_change = ChangeOperation(
            operation=OperationType.CREATE,
            entity_type=EntityType.TOPIC,
            entity_id="topic-123",
            data=MagicMock(),
        )

        changes = [failing_change]

        # Act
        failed_changes = change_processor.process_changes(changes)

        # Assert
        assert len(failed_changes) == 1
        assert failed_changes[0] == failing_change
        create_strategy_mock.process.assert_called_once_with(failing_change)
        assert mock_logger.called

    @patch("logging.Logger.error")
    def test_processing_with_exceptions(self, mock_logger, change_processor):
        """Test that exceptions during processing are caught and logged properly."""
        # Arrange
        delete_strategy_mock = MagicMock()
        delete_strategy_mock.process.side_effect = Topic.DoesNotExist(
            "Topic does not exist"
        )

        change_processor._strategies = {
            OperationType.DELETE: delete_strategy_mock,
        }

        error_change = ChangeOperation(
            operation=OperationType.DELETE,
            entity_type=EntityType.TOPIC,
            entity_id="nonexistent-topic",
            data=None,
        )

        changes = [error_change]

        # Act
        failed_changes = change_processor.process_changes(changes)

        # Assert
        assert len(failed_changes) == 1
        assert failed_changes[0] == error_change
        delete_strategy_mock.process.assert_called_once_with(error_change)
        assert mock_logger.called

    @patch("logging.Logger.error")
    def test_processing_with_mixed_results(self, mock_logger, change_processor):
        """Test processing with a mix of successful, failed, and exception-raising changes."""
        # Arrange
        create_strategy_mock = MagicMock()
        create_strategy_mock.process.return_value = True

        update_strategy_mock = MagicMock()
        update_strategy_mock.process.return_value = False  # This one fails

        delete_strategy_mock = MagicMock()
        delete_strategy_mock.process.side_effect = SubTopic.DoesNotExist(
            "SubTopic does not exist"
        )

        change_processor._strategies = {
            OperationType.CREATE: create_strategy_mock,
            OperationType.UPDATE: update_strategy_mock,
            OperationType.DELETE: delete_strategy_mock,
        }

        successful_change = ChangeOperation(
            operation=OperationType.CREATE,
            entity_type=EntityType.TOPIC,
            entity_id="topic-123",
            data=MagicMock(),
        )

        failed_change = ChangeOperation(
            operation=OperationType.UPDATE,
            entity_type=EntityType.SUBTOPIC,
            entity_id="subtopic-456",
            data=MagicMock(),
        )

        exception_change = ChangeOperation(
            operation=OperationType.DELETE,
            entity_type=EntityType.SUBTOPIC,
            entity_id="nonexistent-subtopic",
            data=None,
        )

        changes = [successful_change, failed_change, exception_change]

        # Act
        failed_changes = change_processor.process_changes(changes)

        # Assert
        assert len(failed_changes) == 2
        assert failed_change in failed_changes
        assert exception_change in failed_changes
        create_strategy_mock.process.assert_called_once_with(successful_change)
        update_strategy_mock.process.assert_called_once_with(failed_change)
        delete_strategy_mock.process.assert_called_once_with(exception_change)
        assert mock_logger.call_count == 2
