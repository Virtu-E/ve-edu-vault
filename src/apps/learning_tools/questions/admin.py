from django.contrib import admin
from django.db import transaction
from django.db.models import JSONField
from django_json_widget.widgets import JSONEditorWidget

from .models import DefaultQuestionSet, QuestionCategory, UserQuestionSet


class JsonWidgetModelAdmin(admin.ModelAdmin):
    formfield_overrides = {JSONField: {"widget": JSONEditorWidget}}


@admin.register(UserQuestionSet)
class UserQuestionSetAdmin(JsonWidgetModelAdmin):
    list_display = ["user", "learning_objective"]
    search_fields = ["user__username", "learning_objective__name"]
    raw_id_fields = ["user", "learning_objective"]

    list_select_related = ["user", "learning_objective"]

    def get_queryset(self, request):
        """Optimize queries by selecting related objects"""
        qs = super().get_queryset(request)
        return qs.select_related("user", "learning_objective")


@admin.register(DefaultQuestionSet)
class DefaultQuestionSetAdmin(JsonWidgetModelAdmin):
    list_display = ["learning_objective"]
    search_fields = ["learning_objective__name"]
    raw_id_fields = ["learning_objective"]

    list_select_related = ["learning_objective"]

    def get_queryset(self, request):
        """Optimize queries by selecting related objects"""
        qs = super().get_queryset(request)
        return qs.select_related("learning_objective")


@admin.register(QuestionCategory)
class QuestionCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "category_id",
        "learning_objective",
        "get_subtopic",
    )
    list_filter = ("learning_objective__sub_topic",)
    search_fields = ("category_id", "learning_objective__name")
    raw_id_fields = ("learning_objective",)

    fieldsets = (
        ("Category Information", {"fields": ("category_id",)}),
        ("Relationships", {"fields": ("learning_objective",)}),
    )

    # Enhanced performance optimization - select deeper relationships
    list_select_related = (
        "learning_objective",
        "learning_objective__sub_topic",
        "learning_objective__sub_topic__topic",
        "learning_objective__sub_topic__topic__course",  # Add course if accessed
    )

    def get_queryset(self, request):
        """Optimize queries by selecting all related objects used in display"""
        qs = super().get_queryset(request)
        return qs.select_related(
            "learning_objective",
            "learning_objective__sub_topic",
            "learning_objective__sub_topic__topic",
            "learning_objective__sub_topic__topic__course",
        )

    def get_subtopic(self, obj):
        """Get the subtopic name for display in the admin list"""
        return obj.learning_objective.sub_topic.name

    get_subtopic.short_description = "SubTopic"
    get_subtopic.admin_order_field = "learning_objective__sub_topic__name"

    def save_model(self, request, obj, form, change):
        """
        Override save_model to ensure transaction handling is consistent
        with the model's save method
        """
        with transaction.atomic():
            super().save_model(request, obj, form, change)
