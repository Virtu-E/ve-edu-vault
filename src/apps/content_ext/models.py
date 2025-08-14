from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from src.apps.core.content.models import SubTopic, Topic
from src.apps.core.users.models import EdxUser


class SubTopicExt(models.Model):
    """Extends the SubTopic model with additional educational metadata"""

    sub_topic = models.OneToOneField(
        SubTopic, on_delete=models.CASCADE, related_name="extension"
    )

    description = models.TextField(help_text="Description of the sub-topic")

    estimated_duration = models.PositiveIntegerField(
        help_text="Estimated time to complete the sub-topic in minutes",
        validators=[MinValueValidator(5), MaxValueValidator(300)],
        default=30,
    )

    metadata = models.JSONField(
        help_text="Additional configurable metadata for the sub-topic",
        default=dict,
        blank=True,
    )

    assessment_criteria = models.JSONField(
        help_text="Criteria for assessing sub-topic mastery",
        default=list,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sub-topic Extension"
        verbose_name_plural = "Sub-topic Extensions"

    def __str__(self):
        return f"{self.sub_topic.name} Extension"

    def __repr__(self):
        return f"<SubTopicExt: id={self.id}, sub_topic='{self.sub_topic.name}', duration={self.estimated_duration}>"


class TopicExt(models.Model):
    """
    Extends the Topic model with additional metadata including detailed description,
    mastery points, and learning path information.
    """

    topic = models.OneToOneField(
        Topic, on_delete=models.CASCADE, related_name="extension"
    )

    description = models.TextField(
        help_text="Comprehensive description of the topic and its importance",
        blank=True,
    )

    base_mastery_points = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(1)],
        help_text="Base points awarded for completing this topic",
    )

    estimated_hours = models.PositiveIntegerField(
        default=0, help_text="Estimated hours to achieve mastery"
    )

    teacher_guide = models.TextField(
        blank=True, help_text="Guidance for teachers on topic instruction"
    )

    minimum_mastery_percentage = models.PositiveIntegerField(
        default=70,  # More sensible default than 0
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Minimum percentage required for topic mastery",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Topic Extension"
        verbose_name_plural = "Topic Extensions"

    def __str__(self):
        return f"{self.topic.name} Extension"

    def __repr__(self):
        return f"<TopicExt: id={self.id}, topic='{self.topic.name}', mastery_points={self.base_mastery_points}, hours={self.estimated_hours}>"


class TopicMastery(models.Model):
    """
    Tracks detailed user progress and mastery for a specific topic,
    including points earned, achievements, and mastery status.
    """

    user = models.ForeignKey(
        EdxUser, on_delete=models.CASCADE, related_name="topic_masteries"
    )

    topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name="user_masteries"
    )

    points_earned = models.PositiveIntegerField(
        default=0, help_text="Total points earned in this topic"
    )

    mastery_achievements = models.JSONField(
        default=dict,
        help_text="Dictionary of specific achievements earned in this topic",
        blank=True,
    )

    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    MASTERY_STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("mastered", "Mastered"),
        ("needs_review", "Needs Review"),
    ]

    mastery_status = models.CharField(
        max_length=20,
        choices=MASTERY_STATUS_CHOICES,
        default="not_started",
    )

    class Meta:
        verbose_name = "User Topic Mastery"
        verbose_name_plural = "User Topic Masteries"

        constraints = [
            models.UniqueConstraint(
                fields=["user", "topic"], name="unique_user_topic_mastery"
            )
        ]

        indexes = [
            models.Index(
                fields=["user", "mastery_status"], name="topicmastery_user_status_idx"
            ),
            models.Index(
                fields=["user", "last_activity"], name="topicmastery_user_activity_idx"
            ),
            models.Index(fields=["mastery_status"], name="topicmastery_status_idx"),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.topic.name} Mastery"

    def __repr__(self):
        return (
            f"<TopicMastery: id={self.id}, "
            f"user='{self.user.username}', "
            f"topic='{self.topic.name}', "
            f"status='{self.mastery_status}', "
            f"points={self.points_earned}>"
        )

    def save(self, *args, **kwargs):
        """Custom save method to handle completion timestamp"""
        if self.mastery_status == "mastered" and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.mastery_status != "mastered":
            self.completed_at = None
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """Check if the mastery record shows recent activity"""
        if not self.last_activity:
            return False
        return (timezone.now() - self.last_activity).days <= 30

    @property
    def progress_percentage(self):
        """Calculate progress percentage based on topic's base mastery points"""
        if (
            hasattr(self.topic, "extension")
            and self.topic.extension.base_mastery_points > 0
        ):
            return min(
                100,
                (self.points_earned / self.topic.extension.base_mastery_points) * 100,
            )
        return 0
