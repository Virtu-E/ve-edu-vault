from django.db import models

from ai_core.performance_calculators import log
from data_types.course_ware_schema import QuestionMetadata
from exceptions import VersionParsingError

# TODO : update the documentation below after alpha release --> things might have changes
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


class User(models.Model):
    id = models.PositiveIntegerField(
        primary_key=True, unique=True, help_text="edX user ID"
    )
    username = models.CharField(
        null=True, blank=True, max_length=100, unique=True, help_text="edX username"
    )
    email = models.EmailField(null=True, blank=True, help_text="edX email")
    # In case i need them in future
    # edx_data = models.JSONField(
    #     db_index=True, null=True, blank=True,
    #     help_text="edX user metadata"
    # )
    # data = models.JSONField(
    #     db_index=True, null=True, blank=True,
    #     help_text="Additional user metadata"
    # )
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "edX User"
        verbose_name_plural = "edX Users"

    def __str__(self):
        return self.username


class AcademicClass(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Course(models.Model):
    """
    Stores open edx course information.
    """

    name = models.CharField(max_length=255)
    course_key = models.CharField(max_length=255, unique=True)
    course_outline = models.JSONField()

    def __str__(self):
        return self.name


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
    block_id = models.TextField(unique=True, db_index=True, null=False, blank=False)
    academic_class = models.ForeignKey(AcademicClass, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    course = models.OneToOneField(Course, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Question Category"
        verbose_name_plural = "Question Categories"
        unique_together = ("examination_level", "academic_class", "course")

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
    block_id = models.TextField(unique=True, db_index=True, null=False, blank=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # This does not make sense, it has to be deleted
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
    # Example of data stored in the field
    # [
    #     {"id": "question_id_1"},
    #     {"id": "question_id_2"},
    #     {"id": "question_id_3"}
    # ]
    question_set_ids = models.JSONField(help_text="References to MongoDB question IDs.")

    class Meta:
        verbose_name = "User Question Set"
        verbose_name_plural = "User Question Sets"

    @property
    def get_question_set_ids(self) -> list[str]:
        """
        Retrieve a list of question set IDs as strings.

        This property processes the `question_set_ids` attribute,
        which is expected to be a list of dictionaries containing an "id" key,
        and returns a list of the "id" values as strings.

        Returns:
            list[str]: A list of question set IDs in string format.
        """
        return [str(item["id"]) for item in self.question_set_ids]

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
    # the data is stored in this format :  dict[str, dict[str, QuestionMetadata | Any]]. Check in data types module
    # for more info ( course_ware_schema.py )
    question_metadata = models.JSONField(
        help_text="Metadata for questions attempted by the user.",
        default={"v1.0.0": {}},
    )

    class Meta:
        verbose_name = "User Question Attempt"
        verbose_name_plural = "User Questions Attempts"

    @staticmethod
    def _parse_version(version: str) -> tuple:
        """
        Parse version string into tuple of integers.

        Args:
            version: Version string (e.g., 'v1.0.0')

        Returns:
            Tuple of integers representing version components
        """
        try:
            parts = version.lstrip("v").split(".")
            return tuple(map(int, parts))
        except (ValueError, AttributeError):
            log.error("Unable to parse version string %s", version)
            raise (VersionParsingError(version))

    @property
    def get_latest_question_metadata(self) -> dict[str, QuestionMetadata]:
        """
        Get the current (latest) question version from metadata.

        Returns:
            Dictionary containing the question metadata (
               -> Top-level key: Question ID,
               -> Second-level key: QuestionMetadata )
        """
        latest_version = max(self.question_metadata.keys(), key=self._parse_version)
        return self.question_metadata[latest_version]

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
    # TODO : retire the is_completed field below because it is redundant
    is_completed = models.BooleanField(default=False)

    @property
    def get_cleared_topics_count(self):
        return self.category.topic_set.filter(is_completed=True).count()

    @property
    def get_topics_count(self):
        return self.category.topics.count()

    @property
    def progress_percentage(self):
        total_topics = self.get_topics_count()
        completed_topics = self.get_cleared_topics_count()
        return (completed_topics / total_topics) * 100 if total_topics > 0 else 0

    class Meta:
        verbose_name = "User Progress"
        verbose_name_plural = "User Progress"

    def __str__(self):
        return f"{self.user.username} - {self.category.name} Progress"
