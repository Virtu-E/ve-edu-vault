import re
from typing import Any, Literal, Union

from django.core.exceptions import ValidationError
from django.db import models

from ai_core.performance.calculators.performance_calculators import log
from edu_vault.settings import common
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


# TODO : formalize academic classes -- how they should look etc

DEFAULT_VERSION = "v1.0.0"
VERSION_PATTERN = re.compile(r"v(\d+)\.(\d+)\.(\d+)")


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


class CoreElement(models.Model):
    """
    Core curriculum element representing a subject area or theme (e.g. Algebra, Geometry)
    """

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


class Category(models.Model):
    """
    Represents a unique question category within an academic class, course and examination level.
    For example, "Quadratic Equations".
    """

    name = models.CharField(max_length=100)
    examination_level = models.CharField(
        choices=EXAMINATION_LEVELS, max_length=20, default="MSCE"
    )
    block_id = models.TextField(unique=True, db_index=True, null=False, blank=False)
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
        verbose_name = "Skill"
        verbose_name_plural = "Skills"

    def __str__(self):
        return f"{self.name} - {self.academic_class}"


class Topic(models.Model):
    """
    Represents a topic or theme under a category. For example, "Completing the Square".
    """

    name = models.CharField(max_length=100)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="topics"
    )
    block_id = models.TextField(
        unique=True, db_index=True, null=False, blank=False
    )  # edx block ID associated with the topic
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Learning Objective"
        verbose_name_plural = "Learning Objectives"

    def __str__(self):
        return f"{self.category.name} - {self.name} - {self.category.academic_class}"


class TopicIframeID(models.Model):
    """
    Model that holds the topic unique iframe identifier.
    """

    identifier = models.CharField(max_length=255, unique=True, db_index=True)
    topic = models.OneToOneField(
        Topic, on_delete=models.CASCADE, related_name="iframe_id"
    )


class BaseQuestionSet(models.Model):
    """Base abstract model for question sets."""

    topic = models.OneToOneField(Topic, on_delete=models.CASCADE)
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

    def clean_question_list_ids(self):
        if len(self.question_list_ids) != getattr(
            common, "MINIMUM_QUESTIONS_THRESHOLD", 9
        ):
            raise ValidationError(
                f"Question set must contain exactly 9 questions. Current count: {len(self.question_list_ids)}"
            )
        return self.question_list_ids

    def clean(self):
        cleaned_data = super().clean()
        self.clean_question_list_ids()
        return cleaned_data


class UserQuestionSet(BaseQuestionSet):
    """User-specific question set."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="question_sets"
    )

    class Meta:
        verbose_name = "User Question Set"
        verbose_name_plural = "User Question Sets"
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    question_list_ids__len=getattr(
                        common, "MINIMUM_QUESTIONS_THRESHOLD", 9
                    )
                ),
                name="user_question_list_length_check",
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.topic.name}"


class DefaultQuestionSet(BaseQuestionSet):
    """Default question set for new users."""

    class Meta:
        verbose_name = "Default Question Set"
        verbose_name_plural = "Default Question Sets"
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    question_list_ids__len=getattr(
                        common, "MINIMUM_QUESTIONS_THRESHOLD", 9
                    )
                ),
                name="default_question_list_length_check",
            )
        ]

    def __str__(self):
        return f"{self.topic.name} Default Question Set"


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

    question_metadata_description = models.JSONField(
        help_text="Stores status information and guidance for questions",
        default={
            "v1.0.0": {
                "status": "Not Started",
                "guidance": "Complete the practice set to assess your knowledge level",
                "learning_mode": "normal",
                "mode_guidance": "Answer and complete 2 out of 3 questions for each difficulty level (easy, medium, and hard) to finish the section.",
            }
        },
    )

    class Meta:
        verbose_name = "User Question Attempt"
        verbose_name_plural = "User Questions Attempts"

    @property
    def get_learning_mode(
        self,
    ) -> Literal["normal", "recovery", "reinforcement", "mastered"]:
        latest_version = self.get_current_version
        return self.question_metadata_description[latest_version]["learning_mode"]

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
    def get_current_version(self) -> str:
        """
        Retrieve the current version based on question metadata.

        Returns:
            str: The current version key with the highest value based on parsing.
        """
        return max(self.question_metadata.keys(), key=self._parse_version)

    @property
    def get_latest_question_metadata(self) -> dict[str, Any]:
        """
        Get the current (latest) question version from metadata.

        Returns:
            Dictionary containing the question metadata (
               -> Top-level key: Question ID,ƒ
               -> Second-level key: QuestionMetadata )
        """
        return self.question_metadata[self.get_current_version]

    @property
    def get_correct_questions_count(self) -> int:
        question_metadata = self.get_latest_question_metadata
        correct_count = len([q for q in question_metadata.values() if q["is_correct"]])
        return correct_count

    @property
    def get_incorrect_questions_count(self) -> int:
        question_metadata = self.get_latest_question_metadata
        incorrect_count = len(
            [q for q in question_metadata.values() if not q["is_correct"]]
        )
        return incorrect_count

    @property
    def get_next_version(self) -> str:
        """
        Generates the next version number based on existing versions.

        Returns:
            Next version string in the format "vX.Y.Z"
        """

        versions = self.question_metadata

        if not versions:
            return DEFAULT_VERSION

        try:
            version_keys = sorted(
                versions.keys(),
                key=lambda x: [int(i) for i in x.lstrip("v").split(".")],
            )
            latest_version = version_keys[-1]

            if match := VERSION_PATTERN.match(latest_version):
                major = int(match.group(1))
                return f"v{major + 1}.0.0"

            log.error("Unable to parse version string %s", latest_version)
            raise VersionParsingError(
                "Unable to parse version string %s", latest_version
            )

        except Exception as e:
            log.error(f"Version parsing error: {str(e)}")
            raise VersionParsingError(f"Version parsing error: {str(e)}")

    @property
    def get_questions_by_status(self) -> list[dict[str, Union[str, int]]]:
        """
        Returns a list of questions with their status (correct, incorrect, or unattempted)
        and question text from the latest question metadata.

        Returns:
            List of dictionaries, each containing:
            - id: Question ID (number)
            - status: Status of the question (correct/incorrect/unattempted)
            - text: Question text
        """
        question_metadata = self.get_latest_question_metadata
        questions_list = []

        for question_id, metadata in question_metadata.items():
            questions_list.append(
                {
                    "id": str(question_id),
                    "status": "correct" if metadata.get("is_correct") else "incorrect",
                    "question_pos": 10,
                }
            )

        return questions_list

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
