from django.db import models

from src.apps.core.courses.models import ExaminationLevel, AcademicClass, Course


# Create your models here.


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


class Topic(models.Model):
    """
    Represents a unique question topic within an academic class, course and examination level.
    For example, "Quadratic Equations".
    """

    name = models.CharField(max_length=255)
    examination_level = models.ForeignKey(ExaminationLevel, on_delete=models.CASCADE)
    block_id = models.TextField(unique=True, db_index=True)
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
    block_id = models.TextField(
        unique=True,
        db_index=True,
    )  # edx block ID associated with the topic
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subtopic"
        verbose_name_plural = "Subtopics"

    def __str__(self):
        return f"SubTopic: {self.name} - Class: {self.topic.academic_class}"


class LearningObjective(models.Model):
    """
    Represents a specific learning goal tied to a subtopic.
    For example, "Students should be able to complete the square to solve quadratics."
    """

    name = models.CharField(max_length=255)
    block_id = models.TextField(unique=True, db_index=True)
    sub_topic = models.ForeignKey(
        SubTopic, on_delete=models.CASCADE, related_name="objective"
    )

    def __str__(self):
        return self.name
