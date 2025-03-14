"""
ai_core.course_sync.diff_engine
~~~~~~~~~~~~

Contains code that is used to compare and detect course changes from
edx course outline, implemented using Chain of Responsibility pattern
"""

import logging
from abc import ABC, abstractmethod
from functools import wraps
from typing import List, Optional

from course_sync.data_types import (
    ChangeOperation,
    EdxCourseOutline,
    EntityType,
    OperationType,
)

log = logging.getLogger(__name__)


class BaseDiffHandler(ABC):
    """Base handler for the diff chain of responsibility"""

    def __init__(self):
        self._next_handler = None

    def set_next(self, handler):
        """Set the next handler in the chain"""
        self._next_handler = handler
        return handler

    def process_next(
        self, old_course: Optional[EdxCourseOutline], new_course: EdxCourseOutline
    ) -> List[ChangeOperation]:
        """Process the next handler in the chain if it exists"""
        if self._next_handler:
            return self._next_handler.handle(old_course, new_course)
        return []

    @abstractmethod
    def handle(
        self, old_course: Optional[EdxCourseOutline], new_course: EdxCourseOutline
    ) -> List[ChangeOperation]:
        """Handle the diff operation and decide whether to continue the chain"""
        pass


class CourseDiffHandler(BaseDiffHandler):
    """Course diff handler - handles course-level changes"""

    def handle(
        self, old_course: Optional[EdxCourseOutline], new_course: EdxCourseOutline
    ) -> List[ChangeOperation]:
        """
        Compare old and new course versions and generate change operations.
        If this is a completely new course, stops the chain.

        Args:
            old_course: Previous course outline version (None if this is a new course)
            new_course: Current course outline version

        Returns:
            List of change operations
        """
        changes: List[ChangeOperation] = []

        # Handle case of a completely new course
        if old_course is None:
            log.info("New course detected: %s", new_course.course_id)
            return [
                ChangeOperation(
                    operation=OperationType.CREATE,
                    entity_type=EntityType.COURSE,
                    entity_id=new_course.course_id,
                    data=new_course,
                )
            ]

        # Check course-level changes
        changes.extend(self._diff_course_properties(old_course, new_course))

        # Continue the chain
        changes.extend(self.process_next(old_course, new_course))

        return changes

    def _diff_course_properties(
        self, old_course: EdxCourseOutline, new_course: EdxCourseOutline
    ) -> List[ChangeOperation]:
        """
        Compare course-level properties and generate change operations.

        Args:
            old_course: Previous course outline
            new_course: Current course outline

        Returns:
            List of change operations for course-level properties
        """
        changes = []

        # Currently only checking title changes
        title_changed = old_course.title != new_course.title

        if title_changed:
            log.info("Course title changed: %s", new_course.course_id)
            changes.append(
                ChangeOperation(
                    operation=OperationType.UPDATE,
                    entity_type=EntityType.COURSE,
                    entity_id=new_course.course_id,
                    data=new_course.title,
                )
            )

        return changes


class SubtopicDiffHandler(BaseDiffHandler):
    """
    Subtopic diff handler - runs before topic handler since we need to capture
    subtopic changes before potential topic deletions
    """

    def handle(
        self, old_course: Optional[EdxCourseOutline], new_course: EdxCourseOutline
    ) -> List[ChangeOperation]:
        """
        Compare subtopics between old and new course versions and generate change operations.

        Args:
            old_course: Previous course outline version (None if this is a new course)
            new_course: Current course outline version

        Returns:
            List of change operations
        """
        changes: List[ChangeOperation] = []
        if not old_course:
            return []

        # Diff subtopics
        changes.extend(self._diff_subtopics(old_course, new_course))

        # Continue the chain
        changes.extend(self.process_next(old_course, new_course))

        return changes

    def _diff_subtopics(
        self, old_course: EdxCourseOutline, new_course: EdxCourseOutline
    ) -> List[ChangeOperation]:
        """
        Compare subtopics across all topics and generate change operations.

        Args:
            old_course: Previous course outline
            new_course: Current course outline

        Returns:
            List of change operations for subtopics
        """
        changes = []

        # Compare subtopics for each topic that exists in both versions
        for old_topic in old_course.topics:
            # Find corresponding topic in new course
            new_topic = next(
                (topic for topic in new_course.topics if topic.id == old_topic.id), None
            )

            if new_topic:
                # Get subtopic ID sets
                old_subtopic_ids = {subtopic.id for subtopic in old_topic.sub_topics}
                new_subtopic_ids = {subtopic.id for subtopic in new_topic.sub_topics}

                # Handle deleted subtopics
                for subtopic_id in old_subtopic_ids - new_subtopic_ids:
                    log.info("Subtopic deleted: %s", subtopic_id)
                    changes.append(
                        ChangeOperation(
                            operation=OperationType.DELETE,
                            entity_type=EntityType.SUBTOPIC,
                            entity_id=subtopic_id,
                            data=None,
                        )
                    )

                # Handle created or updated subtopics
                for new_subtopic in new_topic.sub_topics:
                    old_subtopic = next(
                        (
                            subtopic
                            for subtopic in old_topic.sub_topics
                            if subtopic.id == new_subtopic.id
                        ),
                        None,
                    )

                    if old_subtopic is None:
                        # New subtopic
                        log.info("New subtopic detected: %s", new_subtopic.id)
                        changes.append(
                            ChangeOperation(
                                operation=OperationType.CREATE,
                                entity_type=EntityType.SUBTOPIC,
                                entity_id=new_subtopic.id,
                                data=new_subtopic,
                            )
                        )
                    else:
                        # Check for subtopic changes
                        name_changed = old_subtopic.name != new_subtopic.name

                        if name_changed:
                            log.info("Subtopic name changed: %s", new_subtopic.id)
                            changes.append(
                                ChangeOperation(
                                    operation=OperationType.UPDATE,
                                    entity_type=EntityType.SUBTOPIC,
                                    entity_id=new_subtopic.id,
                                    data=new_subtopic,
                                )
                            )

        return changes


class TopicDiffHandler(BaseDiffHandler):
    """Topic diff handler - handles topic-level changes"""

    def handle(
        self, old_course: Optional[EdxCourseOutline], new_course: EdxCourseOutline
    ) -> List[ChangeOperation]:
        """
        Compare topics between old and new course versions and generate change operations.

        Args:
            old_course: Previous course outline version (None if this is a new course)
            new_course: Current course outline version

        Returns:
            List of change operations
        """
        changes: List[ChangeOperation] = []
        if not old_course:
            return []

        # Diff topics
        changes.extend(self._diff_topics(old_course, new_course))

        # Continue the chain
        changes.extend(self.process_next(old_course, new_course))

        return changes

    def _diff_topics(
        self, old_course: EdxCourseOutline, new_course: EdxCourseOutline
    ) -> List[ChangeOperation]:
        """
        Compare topics between course versions and generate change operations.

        Args:
            old_course: Previous course outline
            new_course: Current course outline

        Returns:
            List of change operations for topics
        """
        changes = []

        # Get topic ID sets
        old_topic_ids = old_course.structure.topics
        new_topic_ids = new_course.structure.topics

        # Handle deleted topics
        for topic_id in old_topic_ids - new_topic_ids:
            log.info("Topic deleted: %s", topic_id)
            changes.append(
                ChangeOperation(
                    operation=OperationType.DELETE,
                    entity_type=EntityType.TOPIC,
                    entity_id=topic_id,
                    data=None,
                )
            )

        # Handle created or updated topics
        for new_topic in new_course.topics:
            old_topic = next(
                (topic for topic in old_course.topics if topic.id == new_topic.id), None
            )

            if old_topic is None:
                # New topic
                log.info("New topic detected: %s", new_topic.id)
                changes.append(
                    ChangeOperation(
                        operation=OperationType.CREATE,
                        entity_type=EntityType.TOPIC,
                        entity_id=new_topic.id,
                        data=new_topic,
                    )
                )
            else:
                # Check for topic changes
                name_changed = old_topic.name != new_topic.name

                if name_changed:
                    log.info("Topic name changed: %s", new_topic.id)
                    changes.append(
                        ChangeOperation(
                            operation=OperationType.UPDATE,
                            entity_type=EntityType.TOPIC,
                            entity_id=new_topic.id,
                            data=new_topic,
                        )
                    )

        return changes


def validate_handlers(func):
    @wraps(func)
    def wrapper(
        self,
        course_handler=CourseDiffHandler,
        subtopic_handler=SubtopicDiffHandler,
        topic_handler=TopicDiffHandler,
        *args,
        **kwargs,
    ):
        # Validate that all handlers are subclasses of BaseDiffHandler
        for handler_class, handler_name in [
            (course_handler, "Course handler"),
            (subtopic_handler, "Subtopic handler"),
            (topic_handler, "Topic handler"),
        ]:
            if not issubclass(handler_class, BaseDiffHandler):
                raise TypeError(
                    f"{handler_name} is invalid: {handler_class.__name__}. Must be a subclass of BaseDiffHandler"
                )

        return func(
            self, course_handler, subtopic_handler, topic_handler, *args, **kwargs
        )

    return wrapper


class DiffEngine:
    """
    Detect differences between course outline versions and generate change operations.
    Implements Chain of Responsibility pattern.
    """

    def __init__(self):
        # Initialize the chain
        self.chain = self._create_handler_chain()

    @validate_handlers
    def _create_handler_chain(
        self,
        course_handler=CourseDiffHandler,
        subtopic_handler=SubtopicDiffHandler,
        topic_handler=TopicDiffHandler,
    ) -> BaseDiffHandler:
        """Create and connect the chain of handlers"""
        # Order: Course -> Subtopic -> Topic
        course_handler = course_handler()
        subtopic_handler = subtopic_handler()
        topic_handler = topic_handler()

        # Link the chain
        course_handler.set_next(subtopic_handler)
        subtopic_handler.set_next(topic_handler)

        return course_handler

    def diff(
        self, old_course: Optional[EdxCourseOutline], new_course: EdxCourseOutline
    ) -> List[ChangeOperation]:
        """
        Compare old and new course versions and generate change operations.
        Starts the chain of responsibility.

        Args:
            old_course: Previous course outline version (None if this is a new course)
            new_course: Current course outline version

        Returns:
            List of change operations to transform old_course into new_course
        """
        log.info("Starting diff process for course: %s", new_course.course_id)
        return self.chain.handle(old_course, new_course)
