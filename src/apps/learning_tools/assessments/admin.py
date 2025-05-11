from django.contrib import admin
from django.db.models import JSONField
from .models import UserAssessmentAttempt
from django_json_widget.widgets import JSONEditorWidget


# Register your models here.


class JsonWidgetModelAdmin(admin.ModelAdmin):
    formfield_overrides = {JSONField: {"widget": JSONEditorWidget}}


@admin.register(UserAssessmentAttempt)
class UserAssessmentAttemptAdmin(JsonWidgetModelAdmin):
    list_display = [
        "user",
        "learning_objective",
    ]
    search_fields = ["user__username", "learning_objective__name"]
    raw_id_fields = ["user", "learning_objective"]
