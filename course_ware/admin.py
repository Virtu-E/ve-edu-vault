from django.contrib import admin
from django.db.models import JSONField
from django.urls import reverse
from django.utils.html import format_html
from django_json_widget.widgets import JSONEditorWidget

from .models import (
    AcademicClass,
    Category,
    Course,
    DefaultQuestionSet,
    Topic,
    User,
    UserCategoryProgress,
    UserQuestionAttempts,
    UserQuestionSet,
)


# Base admin class with JSON widget configuration
class JsonWidgetModelAdmin(admin.ModelAdmin):
    formfield_overrides = {JSONField: {"widget": JSONEditorWidget}}


@admin.register(Course)
class CourseAdmin(JsonWidgetModelAdmin):
    list_display = ["name", "course_key", "view_skills"]
    search_fields = ["name", "course_key"]

    def view_skills(self, obj):
        url = reverse("admin:course_ware_category_changelist") + f"?course__id={obj.id}"
        return format_html('<a href="{}">View Skills</a>', url)

    view_skills.short_description = "Skills"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    class Meta:
        verbose_name = "Skill"
        verbose_name_plural = "Skills"

    list_display = [
        "name",
        "course",
        "examination_level",
        "academic_class",
        "view_objectives",
        "skill_augments",
    ]
    list_filter = ["course", "examination_level", "academic_class"]
    search_fields = ["name", "course__name"]
    search_help_text = "Search by skill name, academic class, or course key"

    def view_objectives(self, obj):
        url = reverse("admin:course_ware_topic_changelist") + f"?category__id={obj.id}"
        return format_html('<a href="{}">View Learning Objectives</a>', url)

    def skill_augments(self, obj):
        try:
            if hasattr(obj, "extension"):
                url = reverse(
                    "admin:course_ware_ext_categoryext_change", args=[obj.extension.id]
                )
                return format_html('<a href="{}">View Skill Augment</a>', url)

            create_url = reverse("admin:course_ware_ext_categoryext_add")
            return format_html(
                '<a href="{}?category={}">Create Augment</a>', create_url, obj.id
            )
        except Exception:
            create_url = reverse("admin:course_ware_ext_categoryext_add")
            return format_html(
                '<a href="{}?category={}">Create Augment</a>', create_url, obj.id
            )

    view_objectives.short_description = "Learning Objectives"
    skill_augments.short_description = "Skill Augment"


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    class Meta:
        verbose_name = "Learning Objective"
        verbose_name_plural = "Learning Objectives"

    list_display = [
        "name",
        "category",
        "category__course",
        "topic_augments",
        "resource_counts",
    ]
    list_filter = ["category", "category__course"]
    search_fields = ["name", "category__name", "category__course__name"]
    search_help_text = "Search by learning objective name, skill name or course name"

    def topic_augments(self, obj):
        try:
            if hasattr(obj, "extension"):
                url = reverse(
                    "admin:course_ware_ext_topicext_change", args=[obj.extension.id]
                )
                return format_html('<a href="{}">View Topic Augment</a>', url)

            create_url = reverse("admin:course_ware_ext_topicext_add")
            return format_html(
                '<a href="{}?topic={}">Create Augment</a>', create_url, obj.id
            )
        except Exception:
            create_url = reverse("admin:course_ware_ext_topicext_add")
            return format_html(
                '<a href="{}?topic={}">Create Augment</a>', create_url, obj.id
            )

    def resource_counts(self, obj):
        if not hasattr(obj, "extension"):
            return "No resources"

        videos_url = (
            reverse("admin:course_ware_ext_videoresource_add")
            + f"?topic_ext={obj.extension.id}"
        )
        books_url = (
            reverse("admin:course_ware_ext_bookresource_add")
            + f"?topic_ext={obj.extension.id}"
        )
        articles_url = (
            reverse("admin:course_ware_ext_articleresource_add")
            + f"?topic_ext={obj.extension.id}"
        )

        video_count = obj.extension.videoresource.count()
        book_count = obj.extension.bookresource.count()
        article_count = obj.extension.articleresource.count()

        return format_html(
            '<a href="{}">Videos ({})</a> | <a href="{}">Books ({})</a> | <a href="{}">Articles ({})</a>',
            videos_url,
            video_count,
            books_url,
            book_count,
            articles_url,
            article_count,
        )

    topic_augments.short_description = "Topic Augment"
    resource_counts.short_description = "Resources"


@admin.register(UserQuestionSet)
class UserQuestionSetAdmin(JsonWidgetModelAdmin):
    list_display = ["user", "topic"]
    search_fields = ["user__username", "topic__name"]
    raw_id_fields = ["user", "topic"]


@admin.register(DefaultQuestionSet)
class DefaultQuestionSetAdmin(JsonWidgetModelAdmin):
    list_display = ["topic"]
    search_fields = ["topic__name"]
    raw_id_fields = ["topic"]


@admin.register(UserQuestionAttempts)
class UserQuestionAttemptsAdmin(JsonWidgetModelAdmin):
    list_display = [
        "user",
        "topic",
        "get_correct_questions_count",
        "get_incorrect_questions_count",
    ]
    search_fields = ["user__username", "topic__name"]
    raw_id_fields = ["user", "topic"]


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "email", "active"]
    search_fields = ["username", "email"]
    list_filter = ["active"]


@admin.register(UserCategoryProgress)
class UserCategoryProgressAdmin(admin.ModelAdmin):
    list_display = ["user", "category", "progress_percentage", "is_completed"]
    list_filter = ["is_completed"]
    search_fields = ["user__username", "category__name"]


@admin.register(AcademicClass)
class AcademicClassAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]
