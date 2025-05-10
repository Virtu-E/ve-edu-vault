from enum import Enum

from django.db import models


class ExaminationLevelChoices(Enum):
    """Examination levels supported by VirtuEducate"""

    MSCE = "MSCE"
    JCE = "JCE"
    IGSCE = "IGSCE"


CLASS_CHOICES = [
    ("Form 1", "Form 1"),
    ("Form 2", "Form 2"),
    ("Form 3", "Form 3"),
    ("Form 4", "Form 4"),
]


LEVEL_CHOICES = [(mode.value, mode.name) for mode in ExaminationLevelChoices]


# Create your models here.


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
