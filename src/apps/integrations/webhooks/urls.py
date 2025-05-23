from django.urls import path

from src.apps.integrations.webhooks.views import edx_webhook_view, qstash_webhook_view

app_name = "webhook"

urlpatterns = [
    path("edx/", edx_webhook_view, name="edx-webhook"),
    path("assessments/", qstash_webhook_view, name="assessments-webhook"),
]
