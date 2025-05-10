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


# This will give [("active", "ACTIVE"), ("graded", "GRADED")]
ATTEMPT_STATUS_CHOICES = [(mode.value, mode.name) for mode in AttemptStatusEnum]


# TODO : should i add database constraints ?


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
