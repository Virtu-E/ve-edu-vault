from django.contrib.auth.models import User
from django.db import models

EXAMINATION_LEVEL = [
    ("MSCE", "MSCE"),
    ("JCE", "JCE"),
    ("IGCSE", "IGCSE"),
]


# Create your models here.
class UserGradeBook(models.Model):
    """
    Model to store a users grades in relation to a question in a course
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    attempts = models.IntegerField(default=0)
    course_key = models.CharField(max_length=255)
    category = models.TextField()  # question category. e.g. Quadratic Equations
    level = models.CharField(max_length=255, choices=EXAMINATION_LEVEL)
    answered_correctly = models.BooleanField(default=False)
    question_id = models.CharField(max_length=255, unique=True)  # mongo question id
    question = models.TextField()
