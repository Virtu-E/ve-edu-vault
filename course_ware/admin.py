from django.contrib import admin
from django.db import transaction
from django.db.models import JSONField
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django_json_widget.widgets import JSONEditorWidget

from .models import (
    AcademicClass,
    Course,
    DefaultQuestionSet,
    EdxUser,
    ExaminationLevel,
    LearningObjective,
    QuestionCategory,
    SubTopic,
    Topic,
    UserAssessmentAttempt,
    UserQuestionSet,
)


# Base admin class with JSON widget configuration
class JsonWidgetModelAdmin(admin.ModelAdmin):
    formfield_overrides = {JSONField: {"widget": JSONEditorWidget}}


@admin.register(Course)
class CourseAdmin(JsonWidgetModelAdmin):
    list_display = ["name", "course_key", "view_topics"]
    search_fields = ["name", "course_key"]

    def view_topics(self, obj):
        url = reverse("admin:course_ware_topic_changelist") + f"?course__id={obj.id}"
        return format_html('<a href="{}">View Topics</a>', url)

    view_topics.short_description = "Topics"


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "course",
        "examination_level",
        "academic_class",
        "view_subtopics",
        "topic_augments",
    ]
    list_filter = ["course", "examination_level", "academic_class"]
    search_fields = ["name", "course__name"]
    search_help_text = "Search by topic name, academic class, or course key"

    def view_subtopics(self, obj):
        url = reverse("admin:course_ware_subtopic_changelist") + f"?topic__id={obj.id}"
        return format_html('<a href="{}">View Subtopics</a>', url)

    def topic_augments(self, obj):
        try:
            if hasattr(obj, "extension"):
                url = reverse(
                    "admin:course_ware_ext_topicext_change", args=[obj.extension.id]
                )
                return format_html('<a href="{}">View Topic Extension</a>', url)

            create_url = reverse("admin:course_ware_ext_topicext_add")
            return format_html(
                '<a href="{}?topic={}">Create Extension</a>', create_url, obj.id
            )
        except Exception:
            create_url = reverse("admin:course_ware_ext_topicext_add")
            return format_html(
                '<a href="{}?topic={}">Create Extension</a>', create_url, obj.id
            )

    view_subtopics.short_description = "Subtopics"
    topic_augments.short_description = "Topic Extension"


@admin.register(SubTopic)
class SubTopicAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "topic",
        "topic_course",
        "subtopic_augments",
        "view_objectives",  # Add this new field to list_display
    ]
    list_filter = ["topic", "topic__course"]
    search_fields = ["name", "topic__name", "topic__course__name"]
    search_help_text = "Search by subtopic name, topic name or course name"

    def topic_course(self, obj):
        return obj.topic.course

    topic_course.short_description = "Course"

    def subtopic_augments(self, obj):
        try:
            if hasattr(obj, "extension"):
                url = reverse(
                    "admin:course_ware_ext_subtopicext_change", args=[obj.extension.id]
                )
                return format_html('<a href="{}">View Subtopic Extension</a>', url)

            create_url = reverse("admin:course_ware_ext_subtopicext_add")
            return format_html(
                '<a href="{}?sub_topic={}">Create Extension</a>', create_url, obj.id
            )
        except Exception:
            create_url = reverse("admin:course_ware_ext_subtopicext_add")
            return format_html(
                '<a href="{}?sub_topic={}">Create Extension</a>', create_url, obj.id
            )

    subtopic_augments.short_description = "Subtopic Extension"

    def view_objectives(self, obj):
        """Display a button to view learning objectives for this subtopic"""
        objectives_count = obj.objective.count()
        if objectives_count > 0:
            # Assuming you have a change list view for LearningObjective
            url = (
                reverse("admin:course_ware_learningobjective_changelist")
                + f"?sub_topic__id__exact={obj.id}"
            )
            return format_html(
                '<a href="{}" class="button">View {} Objective{}</a>',
                url,
                objectives_count,
                "s" if objectives_count > 1 else "",
            )
        else:

            return format_html("No Objectives")

    view_objectives.short_description = "Learning Objectives"


@admin.register(UserQuestionSet)
class UserQuestionSetAdmin(JsonWidgetModelAdmin):
    list_display = ["user", "learning_objective"]
    search_fields = ["user__username", "learning_objective__name"]
    raw_id_fields = ["user", "learning_objective"]


@admin.register(DefaultQuestionSet)
class DefaultQuestionSetAdmin(JsonWidgetModelAdmin):
    list_display = ["learning_objective"]
    search_fields = ["learning_objective__name"]
    raw_id_fields = ["learning_objective"]


@admin.register(UserAssessmentAttempt)
class UserAssessmentAttemptAdmin(JsonWidgetModelAdmin):
    list_display = [
        "user",
        "learning_objective",
    ]
    search_fields = ["user__username", "learning_objective__name"]
    raw_id_fields = ["user", "learning_objective"]


@admin.register(EdxUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "email", "active"]
    search_fields = ["username", "email"]
    list_filter = ["active"]


@admin.register(AcademicClass)
class AcademicClassAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


admin.site.register(ExaminationLevel)


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

    # Nesting fields for better organization in the add/edit form
    fieldsets = (
        ("Category Information", {"fields": ("category_id",)}),
        ("Relationships", {"fields": ("learning_objective",)}),
    )

    # For performance with many records
    list_select_related = (
        "learning_objective",
        "learning_objective__sub_topic",
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


@admin.register(LearningObjective)
class LearningObjectiveAdmin(admin.ModelAdmin):
    list_display = ("name", "block_id", "get_subtopic")
    search_fields = ("name", "block_id", "sub_topic__name")
    raw_id_fields = ("sub_topic",)

    # Nesting fields for better organization in the add/edit form
    fieldsets = (
        ("Learning Objective", {"fields": ("name", "block_id")}),
        ("Relationships", {"fields": ("sub_topic",)}),
    )

    # For performance with many records
    list_select_related = ("sub_topic",)

    def get_subtopic(self, obj):
        """Get the subtopic name for display in the admin list"""
        return obj.sub_topic.name

    get_subtopic.short_description = "SubTopic"
    get_subtopic.admin_order_field = "sub_topic__name"

    def get_queryset(self, request):
        """Optimize queries by prefetching related objects"""
        qs = super().get_queryset(request)
        return qs.select_related("sub_topic")

    # Custom action to view related question categories
    actions = ["view_related_question_categories"]

    def view_related_question_categories(self, request, queryset):
        """Custom admin action to view question categories related to selected objectives"""
        selected = queryset.values_list("id", flat=True)
        url = f"/admin/course_ware/questioncategory/?learning_objective__id__in={','.join(map(str, selected))}"
        return redirect(url)

    view_related_question_categories.short_description = (
        "View related question categories"
    )
