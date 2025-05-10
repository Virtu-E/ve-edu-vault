from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from course_ware.models import EdxUser, SubTopic, Topic


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
        blank=True,
        null=True,
    )

    metadata = models.JSONField(
        help_text="Additional configurable metadata for the sub-topic",
        default=dict,
        blank=True,
        null=True,
    )

    assessment_criteria = models.JSONField(
        help_text="Criteria for assessing sub-topic mastery",
        default=list,
        blank=True,
        null=True,
    )

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
        null=True,
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
        blank=True, null=True, help_text="Guidance for teachers on topic instruction"
    )

    minimum_mastery_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Minimum percentage required for topic mastery",
    )

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
        EdxUser, on_delete=models.CASCADE, related_name="topic_mastery"
    )

    topic = models.OneToOneField(
        Topic, on_delete=models.CASCADE, related_name="topic_mastery"
    )

    points_earned = models.PositiveIntegerField(
        default=0, help_text="Total points earned in this topic"
    )

    mastery_achievements = models.JSONField(
        default=dict,
        help_text="List of specific achievements earned in this category",
    )

    started_at = models.DateTimeField(auto_now_add=True)

    last_activity = models.DateTimeField(auto_now=True)

    completed_at = models.DateTimeField(null=True, blank=True)

    MASTERY_STATUS_CHOICES = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("mastered", "Mastered"),
    ]

    mastery_status = models.CharField(
        max_length=20, choices=MASTERY_STATUS_CHOICES, default="not_started"
    )

    class Meta:
        verbose_name = "User Topic Mastery"
        verbose_name_plural = "User Topic Mastery"

    def __str__(self):
        return f"{self.user.username} - {self.topic.name} Mastery"

    def __repr__(self):
        return (
            f"<TopicMastery: id={self.id}, "
            f"user='{self.user.username}', "
            f"topic='{self.topic.name}',"
            f" status='{self.mastery_status}', "
            f"points={self.points_earned}>"
        )
