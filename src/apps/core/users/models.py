from django.db import models


class EdxUser(models.Model):
    """Holds Edx user information. Not the Django primary user Model"""

    id = models.PositiveIntegerField(
        primary_key=True, unique=True, help_text="edX user ID"
    )
    username = models.CharField(max_length=255, unique=True, help_text="edX username")
    email = models.EmailField(blank=True, help_text="edX email")
    active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "edX User"
        verbose_name_plural = "edX Users"

    def __str__(self):
        return self.username

    @property
    def is_active(self):
        return self.active

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_username(self):
        return self.username
