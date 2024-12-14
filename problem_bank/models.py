from django.contrib.auth.models import User
from django.db import models

"""
In Virtu Educate, challenges and quizzes are organized into categories.
Every quiz or challenge is based on a specific category. For example, there can be a
quiz on the mathematical "Quadratic" category. Within that category, we have topics that represent learning
objectives or skills a user needs to master in order to fully understand the quadratic category.
For every topic, there are questions of varying difficulty that the user must pass to clear the topic.
Once the user has cleared all topics within a category, it indicates that they have mastered the category.

Academic Class and Examination Level
│
├── Category
│   ├── Topic 1
│   │   ├── User Question Set (JSON: Question Set IDs)
│   │   ├── User Topic Attempt (JSON: Attempt Data)
│   │   └── User Progress (Tracks progress for Topic 1)
│   ├── Topic 2
│   │   ├── User Question Set (JSON: Question Set IDs)
│   │   ├── User Topic Attempt (JSON: Attempt Data)
│   │   └── User Progress (Tracks progress for Topic 2)
│   └── ...
│

"""

# Constants for examination levels
EXAMINATION_LEVELS = [
    ("MSCE", "MSCE"),
    ("JCE", "JCE"),
    ("IGCSE", "IGCSE"),
]


class Category(models.Model):
    """
    Represents a unique question category within an academic class, course and examination level.
    For example, "Quadratic Equations".
    """

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    examination_level = models.CharField(
        choices=EXAMINATION_LEVELS, max_length=20, default="MSCE"
    )
    academic_class = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    course_key = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = "Question Category"
        verbose_name_plural = "Question Categories"
        unique_together = ("examination_level", "academic_class", "course_key")

    def __str__(self):
        return self.name


class Topic(models.Model):
    """
    Represents a topic or theme under a category. For example, "Completing the Square".
    """

    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="topics"
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Question Topic"

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class UserQuestionSet(models.Model):
    """
    Represents a user's set of questions related to a specific topic.
    The question set IDs are stored in MongoDB and referenced here.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="question_sets"
    )
    topic = models.OneToOneField(
        Topic, on_delete=models.CASCADE, related_name="question_sets"
    )
    question_set_ids = models.JSONField(help_text="References to MongoDB question IDs.")

    class Meta:
        verbose_name = "User Question Set"
        verbose_name_plural = "User Question Sets"

    def __str__(self):
        return f"{self.user.username} - {self.topic.name}"


class UserQuestionAttempts(models.Model):
    """
    Stores user attempts for questions within a specific topic. Instead of creating a separate table for each question attempt,
    we use a JSON field to store the attempt data. This design choice accommodates the dynamic nature of the questions,
    which can change or be updated at any time based on user progress or other factors.

    Using a JSON field is more efficient than managing hundreds of tables, as it simplifies operations such as deleting,
    modifying, or updating questions without requiring extensive structural changes to the database.
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="question_attempts"
    )
    topic = models.OneToOneField(
        Topic, on_delete=models.CASCADE, related_name="topic_attempts"
    )
    question_metadata = models.JSONField(
        help_text="Metadata for questions attempted by the user."
    )

    class Meta:
        verbose_name = "User Question Attempt"
        verbose_name_plural = "User Questions Attempts"

    def __str__(self):
        return f"{self.user.username} - {self.topic.name} Attempts"


class UserCategoryProgress(models.Model):
    """
    Tracks the user's category progress by keeping track of the cleared/uncleared topics in the category
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="progress")
    category = models.OneToOneField(
        Category, on_delete=models.CASCADE, related_name="category_progress"
    )
    last_activity = models.DateTimeField(auto_now=True)
    total_topics = models.IntegerField(default=0)
    cleared_topics = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)

    class Meta:
        verbose_name = "User Progress"
        verbose_name_plural = "User Progress"

    def __str__(self):
        return f"{self.user.username} - {self.category.name} Progress"
