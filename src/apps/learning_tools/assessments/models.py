import uuid
from enum import Enum
from typing import Optional, Tuple

from django.db import models, transaction

from src.apps.core.content.models import LearningObjective
from src.apps.core.users.models import EdxUser


# Create your models here.
class AttemptStatusEnum(Enum):
    ACTIVE = "active"
    GRADED = "graded"
    PENDING_RESULT = "pending_result"


# This will give [("active", "ACTIVE"), ("graded", "GRADED")]
ATTEMPT_STATUS_CHOICES = [(mode.value, mode.name) for mode in AttemptStatusEnum]


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
    def create_attempt(cls, user, learning_objective) -> "UserAssessmentAttempt":
        attempt = cls.objects.get_or_create(
            user=user,
            learning_objective=learning_objective,
            status=AttemptStatusEnum.ACTIVE.value,
        )
        return attempt

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
