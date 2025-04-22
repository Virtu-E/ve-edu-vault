import logging
import re
from enum import Enum
from typing import Any, Union

from django.db import models, transaction

from ai_core.learning_mode_rules import LearningModeType
from exceptions import VersionParsingError

log = logging.getLogger(__name__)

DEFAULT_VERSION = "v1.0.0"
VERSION_PATTERN = re.compile(r"v(\d+)\.(\d+)\.(\d+)")
LEARNING_MODES = [(mode.name.capitalize(), mode.value) for mode in LearningModeType]


class ExaminationLevelChoices(Enum):
    """Examination levels supported by VirtuEducate"""

    MSCE = "MSCE"
    JCE = "JCE"
    IGSCE = "IGSCE"


LEVEL_CHOICES = [(mode.name, mode.value) for mode in ExaminationLevelChoices]

CLASS_CHOICES = [
    ("Form 1", "Form 1"),
    ("Form 2", "Form 2"),
    ("Form 3", "Form 3"),
    ("Form 4", "Form 4"),
]


class EdxUser(models.Model):
    """Holds Edx user information. Not the Django primary user Model"""

    id = models.PositiveIntegerField(
        primary_key=True, unique=True, help_text="edX user ID"
    )
    username = models.CharField(
        null=True, blank=True, max_length=255, unique=True, help_text="edX username"
    )
    email = models.EmailField(null=True, blank=True, help_text="edX email")
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "edX User"
        verbose_name_plural = "edX Users"

    def __str__(self):
        return self.username


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
    flash_card_description = models.TextField(
        blank=True, default="FlashCard Description"
    )
    block_id = models.TextField(
        unique=True, db_index=True, null=False, blank=False
    )  # edx block ID associated with the topic
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subtopic"
        verbose_name_plural = "Subtopics"

    def __str__(self):
        return f"SubTopic: {self.name} - Class: {self.topic.academic_class}"

    def save(self, *args, **kwargs):
        # to avoid circular import error
        from course_sync.side_effects.tasks import process_subtopic_creation_side_effect

        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            transaction.on_commit(
                lambda: process_subtopic_creation_side_effect.delay(subtopic_id=self.pk)
            )


class SubTopicIframeID(models.Model):
    """
    Model that holds the subtopic unique iframe identifier.
    """

    identifier = models.CharField(max_length=255, unique=True, db_index=True)
    sub_topic = models.OneToOneField(
        SubTopic, on_delete=models.CASCADE, related_name="iframe_id"
    )


class BaseQuestionSet(models.Model):
    """Base abstract model for question sets."""

    sub_topic = models.OneToOneField(SubTopic, on_delete=models.CASCADE)
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
        return f"{self.user.username} - {self.sub_topic.name}"


class DefaultQuestionSet(BaseQuestionSet):
    """Default question set for new users."""

    class Meta:
        verbose_name = "Default Question Set"
        verbose_name_plural = "Default Question Sets"

    def __str__(self):
        return f"Sub Topic: {self.sub_topic.name} Default Question Set"


class UserQuestionAttempts(models.Model):
    """
    Stores user attempts for questions within a specific sub topic.

    Instead of creating a separate table for each question attempt,
    we use a JSON field to store the attempt data. This design choice
    accommodates the dynamic nature of the questions,
    which can change or be updated at any time based on user progress or other factors.
    Using a JSON field is more efficient than managing hundreds of tables,
    as it simplifies operations such as deleting,
    modifying, or updating questions without requiring extensive structural changes to the database.
    """

    user = models.ForeignKey(
        EdxUser, on_delete=models.CASCADE, related_name="question_attempts"
    )
    sub_topic = models.OneToOneField(
        SubTopic, on_delete=models.CASCADE, related_name="sub_topic_attempts"
    )
    # the data is stored in this format :  dict[str, dict[str, QuestionMetadata | Any]]. Check in data types module
    # for more info ( course_ware_schema.py )
    question_metadata = models.JSONField(
        help_text="Metadata for questions attempted by the user.",
        default={"v1.0.0": dict},
    )
    current_learning_mode = models.CharField(
        choices=LEARNING_MODES, default="normal", max_length=255
    )

    # TODO : extract this to Mongo DB
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
    def get_latest_question_metadata(self) -> dict[str, dict | Any]:
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

        except KeyError as e:
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
        return f"{self.user.username} - {self.sub_topic.name} Attempts"
