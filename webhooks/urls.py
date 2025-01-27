from django.urls import path

from webhooks.views import webhook_view

urlpatterns = [
    path("edx/", webhook_view, name="webhook"),
]
