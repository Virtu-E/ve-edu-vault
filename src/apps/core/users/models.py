from django.db import models


# Create your models here.
class EdxUser(models.Model):
    """Holds Edx user information. Not the Django primary user Model"""

    id = models.PositiveIntegerField(
        primary_key=True, unique=True, help_text="edX user ID"
    )
    username = models.CharField(max_length=255, unique=True, help_text="edX username")
    email = models.EmailField(blank=True, help_text="edX email")
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "edX User"
        verbose_name_plural = "edX Users"

    def __str__(self):
        return self.username
