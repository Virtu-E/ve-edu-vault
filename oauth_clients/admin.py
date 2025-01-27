from django import forms
from django.contrib import admin

from .models import OAuthClientConfig


class OAuthClientConfigForm(forms.ModelForm):
    client_id = forms.CharField(
        widget=forms.TextInput(attrs={"autocomplete": "off"}),
        help_text="Will be encrypted when saved",
    )
    client_secret = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "off"}),
        help_text="Will be encrypted when saved",
    )

    class Meta:
        model = OAuthClientConfig
        fields = [
            "name",
            "service_type",
            "base_url",
            "client_id",
            "client_secret",
            "is_active",
            "description",
        ]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        if instance:
            initial = kwargs.get("initial", {})
            initial["client_id"] = instance.client_id
            initial["client_secret"] = instance.client_secret
            kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.client_id = self.cleaned_data["client_id"]
        instance.client_secret = self.cleaned_data["client_secret"]
        if commit:
            instance.save()
        return instance


@admin.register(OAuthClientConfig)
class OAuthClientConfigAdmin(admin.ModelAdmin):
    form = OAuthClientConfigForm
    list_display = ["name", "service_type", "base_url", "is_active", "created_at"]
    list_filter = ["service_type", "is_active"]
    search_fields = ["name", "base_url", "description"]
    readonly_fields = ["created_at", "updated_at"]

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return list(self.readonly_fields) + ["name", "service_type"]
        return self.readonly_fields
