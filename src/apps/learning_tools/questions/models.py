from django.db import models, transaction

from src.apps.core.content.models import LearningObjective
from src.apps.core.users.models import EdxUser


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
        from src.services.course_sync.tasks import add_default_question_set

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
