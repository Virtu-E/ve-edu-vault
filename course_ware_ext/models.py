from django.core.validators import MaxValueValidator, MinValueValidator, URLValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from course_ware.models import Category, Topic, EdxUser


class TopicExt(models.Model):
    """
    Extends the Topic model with additional educational metadata including
    learning objectives, resources, and other pedagogical information.
    """

    topic = models.OneToOneField(Topic, on_delete=models.CASCADE, related_name="extension")

    description = models.TextField(help_text="Description of the topic")

    estimated_duration = models.PositiveIntegerField(
        help_text="Estimated time to complete the topic in minutes",
        validators=[MinValueValidator(5), MaxValueValidator(300)],
        default=30,
        blank=True,
        null=True,
    )

    metadata = models.JSONField(
        help_text="Additional configurable metadata for the topic",
        default=dict,
        blank=True,
        null=True,
    )

    teacher_notes = models.TextField(blank=True, null=True, help_text="Notes and guidance for teachers")

    assessment_criteria = models.JSONField(
        help_text="Criteria for assessing topic mastery",
        default=list,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Learning Objective Extension"
        verbose_name_plural = "Learning Objective Extensions"

    def __str__(self):
        return f"{self.topic.name} - {self.topic.category}"

    @property
    def get_all_resources(self):
        """Returns all resources grouped by type"""
        return {
            "videos": self.videoresource.all(),
            "books": self.bookresource.all(),
            "articles": self.articleresource.all(),
        }

    @property
    def get_featured_resources(self):
        """Returns featured resources of all types"""
        return {
            "videos": self.videoresource.filter(is_featured=True),
            "books": self.bookresource.filter(is_featured=True),
            "articles": self.articleresource.filter(is_featured=True),
        }

    def add_resource(self, resource_type, **resource_data):
        """
        Add a new resource of the specified type
        """
        resource_models = {
            "video": VideoResource,
            "book": BookResource,
            "article": ArticleResource,
        }

        if resource_type not in resource_models:
            raise ValueError(f"Invalid resource type: {resource_type}")

        model_class = resource_models[resource_type]
        resource = model_class(topic_ext=self, **resource_data)
        resource.save()
        return resource


class BaseResource(models.Model):
    """
    Abstract base class for all educational resources
    """

    topic_ext = models.ForeignKey(TopicExt, on_delete=models.CASCADE, related_name="%(class)s")

    title = models.CharField(max_length=255, help_text="Title of the resource")

    description = models.TextField(blank=True, help_text="Description of the resource")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_featured = models.BooleanField(default=False, help_text="Featured resources appear prominently in the UI")

    metadata = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        help_text="Additional metadata specific to the resource",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class VideoResource(BaseResource):
    """
    Model for video-based educational resources
    """

    url = models.URLField(validators=[URLValidator()], help_text="URL of the video")

    duration = models.PositiveIntegerField(
        help_text="Duration of the video in minutes",
        validators=[MinValueValidator(1), MaxValueValidator(480)],  # 8 hours max
    )

    platform = models.CharField(
        max_length=50,
        choices=[("youtube", "YouTube"), ("vimeo", "Vimeo"), ("other", "Other")],
        default="youtube",
    )

    requires_subscription = models.BooleanField(
        default=False,
        help_text="Indicates if the video requires a platform subscription",
    )

    transcript_available = models.BooleanField(default=False, help_text="Indicates if a transcript is available")

    class Meta:
        verbose_name = _("Video Resource")
        verbose_name_plural = _("Video Resources")


class BookResource(BaseResource):
    """
    Model for book-based educational resources
    """

    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=13, blank=True, help_text="International Standard Book Number")
    url = models.URLField(validators=[URLValidator()], help_text="URL to the book")

    publication_year = models.PositiveIntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2100)])

    publisher = models.CharField(max_length=255, blank=True)

    edition = models.CharField(max_length=50, blank=True)

    pages = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="Number of pages in the book")

    format = models.CharField(
        max_length=20,
        choices=[
            ("physical", "Physical Book"),
            ("ebook", "E-Book"),
            ("pdf", "PDF"),
            ("both", "Physical & Digital"),
        ],
        default="physical",
    )

    class Meta:
        verbose_name = _("Book Resource")
        verbose_name_plural = _("Book Resources")


class ArticleResource(BaseResource):
    """
    Model for article-based educational resources
    """

    author = models.CharField(max_length=255)
    url = models.URLField(validators=[URLValidator()], help_text="URL of the article")

    publication_date = models.DateField()

    source = models.CharField(max_length=255, help_text="Source/publisher of the article")

    is_peer_reviewed = models.BooleanField(default=False, help_text="Indicates if the article is peer-reviewed")

    reading_time = models.PositiveIntegerField(
        help_text="Estimated reading time in minutes",
        validators=[MinValueValidator(1), MaxValueValidator(120)],
    )

    class Meta:
        verbose_name = _("Article Resource")
        verbose_name_plural = _("Article Resources")


class CategoryExt(models.Model):
    """
    Extends the Category model with additional metadata including detailed description,
    mastery points, and learning path information.
    """

    category = models.OneToOneField(Category, on_delete=models.CASCADE, related_name="extension")

    description = models.TextField(
        help_text="Comprehensive description of the category and its importance",
        blank=True,
        null=True,
    )

    base_mastery_points = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(1)],
        help_text="Base points awarded for completing this category",
    )

    estimated_hours = models.PositiveIntegerField(default=0, help_text="Estimated hours to achieve mastery")

    teacher_guide = models.TextField(blank=True, null=True, help_text="Guidance for teachers on category instruction")

    minimum_mastery_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Minimum percentage required for category mastery",
    )

    class Meta:
        verbose_name = "Skill Extension"
        verbose_name_plural = "Skill Extensions"

    def __str__(self):
        return f"{self.category.name} Extension"


class TopicMastery(models.Model):
    """
    Tracks detailed user progress and mastery for a specific topic,
    including points earned, achievements, and mastery status.
    """

    user = models.ForeignKey(EdxUser, on_delete=models.CASCADE, related_name="topic_mastery")

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="topic_mastery")

    points_earned = models.PositiveIntegerField(default=0, help_text="Total points earned in this topic")

    mastery_achievements = models.JSONField(
        default=dict(),
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

    mastery_status = models.CharField(max_length=20, choices=MASTERY_STATUS_CHOICES, default="not_started")

    class Meta:
        verbose_name = "User Skill Mastery"
        verbose_name_plural = "User Skill Mastery"

    def __str__(self):
        return f"{self.user.username} - {self.topic.name} Mastery"
