from django.core.exceptions import ValidationError
from django.db import models

from .utils import decrypt_value, encrypt_value


class OAuthClientConfig(models.Model):
    SERVICE_TYPES = [("OPENEDX", "Open edX Instance"), ("OTHER", "Other Service")]

    name = models.CharField(max_length=255, unique=True)
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES)
    base_url = models.URLField(help_text="Service base URL")
    _client_id = models.TextField(db_column="client_id")
    _client_secret = models.TextField(db_column="client_secret")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True)

    @property
    def client_id(self):
        return decrypt_value(self._client_id)

    @client_id.setter
    def client_id(self, value):
        self._client_id = encrypt_value(value)

    @property
    def client_secret(self):
        return decrypt_value(self._client_secret)

    @client_secret.setter
    def client_secret(self, value):
        self._client_secret = encrypt_value(value)

    class Meta:
        verbose_name = "OAuth Client Configuration"
        verbose_name_plural = "OAuth Client Configurations"
        indexes = [
            models.Index(fields=["service_type"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_service_type_display()})"

    def clean(self):
        if self.is_active:
            active_configs = OAuthClientConfig.objects.filter(
                service_type=self.service_type, is_active=True
            ).exclude(pk=self.pk)
            if active_configs.exists():
                raise ValidationError(
                    f"There can only be one active configuration per service type."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
