# Create your models here.
from typing import TypeVar

from django.db import models

ToolConsumerModel = TypeVar("ToolConsumerModel", bound="ToolConsumer")


class ToolConsumer(models.Model):
    issuer = models.CharField(max_length=255, unique=True)
    client_id = models.CharField(max_length=255, unique=True)
    auth_login_url = models.URLField()
    auth_token_url = models.URLField()
    key_set_url = models.URLField()
    private_key = models.TextField()  # TODO : find a smart way of storing the keys here
    public_key = (
        models.TextField()
    )  # TODO : same thing with this field. Need to be encrypted and secure
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
