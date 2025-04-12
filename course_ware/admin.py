from django.contrib import admin
from django.db.models import JSONField
from django.urls import reverse
from django.utils.html import format_html
from django_json_widget.widgets import JSONEditorWidget

from .models import (AcademicClass, Course, DefaultQuestionSet, EdxUser,
                     ExaminationLevel, SubTopic, SubTopicIframeID, Topic,
                     UserQuestionAttempts, UserQuestionSet)


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


@admin.register(UserQuestionSet)
class UserQuestionSetAdmin(JsonWidgetModelAdmin):
    list_display = ["user", "sub_topic"]
    search_fields = ["user__username", "sub_topic__name"]
    raw_id_fields = ["user", "sub_topic"]


@admin.register(DefaultQuestionSet)
class DefaultQuestionSetAdmin(JsonWidgetModelAdmin):
    list_display = ["sub_topic"]
    search_fields = ["sub_topic__name"]
    raw_id_fields = ["sub_topic"]


@admin.register(UserQuestionAttempts)
class UserQuestionAttemptsAdmin(JsonWidgetModelAdmin):
    list_display = [
        "user",
        "sub_topic",
        "get_correct_questions_count",
        "get_incorrect_questions_count",
    ]
    search_fields = ["user__username", "sub_topic__name"]
    raw_id_fields = ["user", "sub_topic"]


@admin.register(EdxUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "email", "active"]
    search_fields = ["username", "email"]
    list_filter = ["active"]


@admin.register(AcademicClass)
class AcademicClassAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(SubTopicIframeID)
class SubTopicIframeIDAdmin(admin.ModelAdmin):
    list_display = ["identifier", "sub_topic"]
    search_fields = ["identifier"]


admin.site.register(ExaminationLevel)
