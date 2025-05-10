import logging
import re
import uuid
from enum import Enum
from typing import Optional, Tuple

from django.db import models, transaction

from ai_core.learning_mode_rules import LearningModeType

log = logging.getLogger(__name__)

DEFAULT_VERSION = "v1.0.0"
VERSION_PATTERN = re.compile(r"v(\d+)\.(\d+)\.(\d+)")
LEARNING_MODES = [(mode.name.capitalize(), mode.value) for mode in LearningModeType]


class AttemptStatusEnum(Enum):
    ACTIVE = "active"
    GRADED = "graded"
    PENDING_RESULT = "pending_result"


class ExaminationLevelChoices(Enum):
    """Examination levels supported by VirtuEducate"""

    MSCE = "MSCE"
    JCE = "JCE"
    IGSCE = "IGSCE"


LEVEL_CHOICES = [(mode.value, mode.name) for mode in ExaminationLevelChoices]

CLASS_CHOICES = [
    ("Form 1", "Form 1"),
    ("Form 2", "Form 2"),
    ("Form 3", "Form 3"),
    ("Form 4", "Form 4"),
]

# This will give [("active", "ACTIVE"), ("graded", "GRADED")]
ATTEMPT_STATUS_CHOICES = [(mode.value, mode.name) for mode in AttemptStatusEnum]





class AcademicClass(models.Model):
    """Holds Academic class information. E.g.: Form 1"""

    name = models.CharField(max_length=255, choices=CLASS_CHOICES, unique=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    """Stores open edx course information."""

    name = models.CharField(max_length=255)
    course_key = models.CharField(max_length=255, unique=True)
    course_outline = models.JSONField()

    def __str__(self):
        return self.name


# TODO : will probably be deprecated
class CoreElement(models.Model):
    """Core curriculum element representing a subject area or theme (e.g. Algebra, Geometry)"""

    name = models.CharField(max_length=255, unique=True)
    tags = models.JSONField(default=dict)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Core Element"
        verbose_name_plural = "Core Elements"

    def __str__(self):
        return self.name


class ExaminationLevel(models.Model):
    """Stores Examination Levels related to the Malawian School system"""

    name = models.CharField(max_length=255, choices=LEVEL_CHOICES, unique=True)

    def __str__(self):
        return self.name


# TODO : should i add database constraints ?
class Topic(models.Model):
    """
    Represents a unique question topic within an academic class, course and examination level.
    For example, "Quadratic Equations".
    """

    name = models.CharField(max_length=255)
    examination_level = models.ForeignKey(ExaminationLevel, on_delete=models.CASCADE)
    block_id = models.TextField(unique=True, db_index=True)
    academic_class = models.ForeignKey(AcademicClass, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="category"
    )
    core_element = models.ForeignKey(
        CoreElement,
        on_delete=models.SET_NULL,
        related_name="core_element",
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Topic"
        verbose_name_plural = "Topics"

    def __str__(self):
        return f"Topic: {self.name} - Class: {self.academic_class}"


class SubTopic(models.Model):
    """
    Represents a subtopic or theme under a topic. For example, "Completing the Square".
    """

    name = models.CharField(max_length=255)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="topics")
    # this field is used to populate the description of the flash cards
    block_id = models.TextField(
        unique=True,
        db_index=True,
    )  # edx block ID associated with the topic
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subtopic"
        verbose_name_plural = "Subtopics"

    def __str__(self):
        return f"SubTopic: {self.name} - Class: {self.topic.academic_class}"


class LearningObjective(models.Model):
    """
    Represents a specific learning goal tied to a subtopic.
    For example, "Students should be able to complete the square to solve quadratics."
    """

    name = models.CharField(max_length=255)
    block_id = models.TextField(unique=True, db_index=True)
    sub_topic = models.ForeignKey(
        SubTopic, on_delete=models.CASCADE, related_name="objective"
    )

    def __str__(self):
        return self.name


class QuestionCategory(models.Model):
    """
    Holds the different unique question categories based on  learning objectives.
    """

    learning_objective = models.OneToOneField(
        LearningObjective, on_delete=models.CASCADE
    )
    category_id = models.CharField(max_length=255, db_index=True)

    class Meta:
        verbose_name = "Question Category"
        verbose_name_plural = "Question Categories"

    def save(self, *args, **kwargs):
        # to avoid circular import error
        from course_sync.tasks import add_default_question_set

        super().save(*args, **kwargs)
        transaction.on_commit(
            lambda: add_default_question_set.delay(
                objective_id=self.learning_objective.id
            )
        )

    def __str__(self):
        return f"{self.learning_objective.name}"


class BaseQuestionSet(models.Model):
    """Base abstract model for question sets."""

    learning_objective = models.OneToOneField(
        LearningObjective, on_delete=models.CASCADE
    )
    """
    Array of question reference objects
    Example:
    [
       {"id": "mongo_question_id_1"},
       {"id": "mongo_question_id_2"},
       {"id": "mongo_question_id_3"}
    ]
    """
    question_list_ids = models.JSONField(
        help_text="References to MongoDB question IDs."
    )

    class Meta:
        abstract = True

    @property
    def get_question_set_ids(self) -> set[str]:
        return {str(item["id"]) for item in self.question_list_ids}


class UserQuestionSet(BaseQuestionSet):
    """User-specific question set."""

    user = models.ForeignKey(
        EdxUser, on_delete=models.CASCADE, related_name="question_sets"
    )
    # gets activated when grading starts.
    grading_mode = models.BooleanField(default=False)

    class Meta:
        verbose_name = "User Question Set"
        verbose_name_plural = "User Question Sets"

    def __str__(self):
        return f"{self.user.username} - {self.learning_objective.name}"


class DefaultQuestionSet(BaseQuestionSet):
    """Default question set for new users."""

    class Meta:
        verbose_name = "Default Question Set"
        verbose_name_plural = "Default Question Sets"

    def __str__(self):
        return f"Sub Topic: {self.learning_objective.name} Default Question Set"


class UserAssessmentAttempt(models.Model):
    """
    Stores user attempts for questions in a learning_objective.
    """

    user = models.ForeignKey(
        EdxUser, on_delete=models.CASCADE, related_name="assessment_attempts"
    )
    # unique UUID per assessment
    assessment_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    learning_objective = models.ForeignKey(
        LearningObjective, on_delete=models.CASCADE, related_name="attempts"
    )
    status = models.CharField(
        max_length=20,
        choices=ATTEMPT_STATUS_CHOICES,
        default=AttemptStatusEnum.ACTIVE.value,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Assessment Attempt"
        verbose_name_plural = "User Assessment Attempts"
        constraints = [
            # Ensure only one active attempt per user-objective pair
            models.UniqueConstraint(
                fields=["user", "learning_objective"],
                condition=models.Q(status=AttemptStatusEnum.ACTIVE.value),
                name="unique_active_attempt",
            )
        ]

    @classmethod
    def get_active_attempt(
        cls, user, learning_objective
    ) -> Optional["UserAssessmentAttempt"]:
        """
        Get the active attempt for user and learning objective if it exists.

        Args:
            user: The user to check
            learning_objective: The learning objective

        Returns:
            The active attempt or None if no active attempt exists
        """
        try:
            return cls.objects.get(
                user=user,
                learning_objective=learning_objective,
                status=AttemptStatusEnum.ACTIVE.value,
            )
        except cls.DoesNotExist:
            return None

    @classmethod
    def has_active_attempt(cls, user, learning_objective) -> bool:
        """Check if the user has an active attempt for this learning objective"""
        return cls.get_active_attempt(user, learning_objective) is not None

    @classmethod
    def get_or_create_attempt(
        cls, user, learning_objective, **kwargs
    ) -> Tuple["UserAssessmentAttempt", bool]:
        """Get existing active attempt or create a new one if none exists"""

        with transaction.atomic():
            attempt, created = cls.objects.get_or_create(
                user=user,
                learning_objective=learning_objective,
                status=AttemptStatusEnum.ACTIVE.value,
                defaults=kwargs,
            )
            return attempt, created

    def mark_as_graded(self) -> None:
        """Mark this attempt as graded/completed"""
        self.status = AttemptStatusEnum.GRADED.value
        self.save(update_fields=["status", "updated_at"])
