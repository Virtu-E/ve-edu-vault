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


class ExaminationLevel(models.Model):
    """Stores Examination Levels related to the Malawian School system"""

    name = models.CharField(max_length=255, choices=LEVEL_CHOICES, unique=True)

    def __str__(self):
        return self.name
