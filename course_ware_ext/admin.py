from django.contrib import admin
from django.db.models import JSONField
from django_json_widget.widgets import JSONEditorWidget

from .models import SubTopicExt, TopicExt


class JsonWidgetModelAdmin(admin.ModelAdmin):
    formfield_overrides = {JSONField: {"widget": JSONEditorWidget}}


@admin.register(TopicExt)
class TopicExtAdmin(admin.ModelAdmin):
    list_display = ["topic", "base_mastery_points", "estimated_hours"]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "topic",
                    "description",
                    "base_mastery_points",
                    "estimated_hours",
                    "minimum_mastery_percentage",
                )
            },
        ),
        (
            "Teaching Information",
            {
                "fields": ("teacher_guide",),
            },
        ),
    )


@admin.register(SubTopicExt)
class SubTopicExtAdmin(JsonWidgetModelAdmin):
    list_display = ("sub_topic", "estimated_duration")
    search_fields = ("sub_topic__name",)
    raw_id_fields = ("sub_topic",)
    autocomplete_fields = ["sub_topic"]

    fieldsets = (
        ("Basic Information", {"fields": ("sub_topic", "description")}),
        ("Time Estimation", {"fields": ("estimated_duration",)}),
        ("Additional Information", {"fields": ("metadata", "assessment_criteria")}),
    )
