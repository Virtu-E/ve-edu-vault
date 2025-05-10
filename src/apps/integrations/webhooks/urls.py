from django.urls import path

from src.apps.integrations.webhooks.views import webhook_view

urlpatterns = [
    path("edx/", webhook_view, name="webhook"),
    path("assessments/", webhook_view, name="assessments-webhook"),
]
