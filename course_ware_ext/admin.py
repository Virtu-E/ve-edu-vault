from django.contrib import admin
from django.db.models import JSONField
from django.urls import reverse
from django.utils.html import format_html
from django_json_widget.widgets import JSONEditorWidget

from .models import ArticleResource, BookResource, CategoryExt, TopicExt, VideoResource


# Base admin class with JSON widget configuration
class JsonWidgetModelAdmin(admin.ModelAdmin):
    formfield_overrides = {JSONField: {"widget": JSONEditorWidget}}


@admin.register(VideoResource)
class VideoResourceAdmin(JsonWidgetModelAdmin):
    list_display = (
        "title",
        "platform",
        "duration",
        "is_featured",
        "requires_subscription",
    )
    list_filter = (
        "platform",
        "is_featured",
        "requires_subscription",
        "transcript_available",
    )
    search_fields = ("title", "description")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Basic Information",
            {"fields": ("topic_ext", "title", "description", "is_featured")},
        ),
        ("Video Details", {"fields": ("url", "platform", "duration")}),
        (
            "Additional Information",
            {"fields": ("requires_subscription", "transcript_available", "metadata")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(BookResource)
class BookResourceAdmin(JsonWidgetModelAdmin):
    list_display = ("title", "author", "publication_year", "format", "is_featured")
    list_filter = ("format", "is_featured", "publication_year")
    search_fields = ("title", "author", "isbn", "publisher")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Basic Information",
            {"fields": ("topic_ext", "title", "description", "is_featured")},
        ),
        (
            "Book Details",
            {
                "fields": (
                    "author",
                    "url",
                    "isbn",
                    "publication_year",
                    "publisher",
                    "edition",
                    "pages",
                    "format",
                )
            },
        ),
        ("Additional Information", {"fields": ("metadata",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ArticleResource)
class ArticleResourceAdmin(JsonWidgetModelAdmin):
    list_display = (
        "title",
        "author",
        "publication_date",
        "reading_time",
        "is_peer_reviewed",
        "is_featured",
    )
    list_filter = ("is_peer_reviewed", "is_featured", "publication_date")
    search_fields = ("title", "author", "source")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Basic Information",
            {"fields": ("topic_ext", "title", "description", "is_featured")},
        ),
        (
            "Article Details",
            {"fields": ("author", "url", "publication_date", "source", "reading_time")},
        ),
        ("Additional Information", {"fields": ("is_peer_reviewed", "metadata")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(TopicExt)
class TopicExtAdmin(admin.ModelAdmin):
    list_display = ["topic", "estimated_duration", "resource_summary"]
    readonly_fields = ["resource_summary"]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "topic",
                    "description",
                    "estimated_duration",
                    "metadata",
                    "teacher_notes",
                    "assessment_criteria",
                )
            },
        ),
        (
            "Resources",
            {
                "fields": ("resource_summary",),
                "description": "Manage resources for this topic",
            },
        ),
    )

    def resource_summary(self, obj):
        if not obj.pk:  # If this is a new object being created
            return "Save the topic extension first to add resources"

        videos_url = (
            reverse("admin:course_ware_ext_videoresource_add") + f"?topic_ext={obj.pk}"
        )
        books_url = (
            reverse("admin:course_ware_ext_bookresource_add") + f"?topic_ext={obj.pk}"
        )
        articles_url = (
            reverse("admin:course_ware_ext_articleresource_add")
            + f"?topic_ext={obj.pk}"
        )

        video_list_url = (
            reverse("admin:course_ware_ext_videoresource_changelist")
            + f"?topic_ext__id__exact={obj.pk}"
        )
        book_list_url = (
            reverse("admin:course_ware_ext_bookresource_changelist")
            + f"?topic_ext__id__exact={obj.pk}"
        )
        article_list_url = (
            reverse("admin:course_ware_ext_articleresource_changelist")
            + f"?topic_ext__id__exact={obj.pk}"
        )

        video_count = obj.videoresource.count()
        book_count = obj.bookresource.count()
        article_count = obj.articleresource.count()

        return format_html(
            """
            <div style="margin-bottom: 10px;">
                <strong>Videos:</strong>
                <a href="{}">View All ({})</a> |
                <a href="{}" class="addlink">Add New</a>
            </div>
            <div style="margin-bottom: 10px;">
                <strong>Books:</strong>
                <a href="{}">View All ({})</a> |
                <a href="{}" class="addlink">Add New</a>
            </div>
            <div style="margin-bottom: 10px;">
                <strong>Articles:</strong>
                <a href="{}">View All ({})</a> |
                <a href="{}" class="addlink">Add New</a>
            </div>
            """,
            video_list_url,
            video_count,
            videos_url,
            book_list_url,
            book_count,
            books_url,
            article_list_url,
            article_count,
            articles_url,
        )

    resource_summary.short_description = "Resources"


@admin.register(CategoryExt)
class CategoryExtAdmin(admin.ModelAdmin):
    list_display = ("category", "base_mastery_points")
    search_fields = (
        "category__name",
        "category__academic_class",
        "category__course__course_key",
    )
    raw_id_fields = ("category",)
    autocomplete_fields = ["category"]
    readonly_fields = [
        "base_mastery_points",
        "minimum_mastery_percentage",
    ]
    fieldsets = (
        ("Basic Information", {"fields": ("category", "description")}),
        (
            "Mastery Settings",
            {
                "fields": (
                    "base_mastery_points",
                    "minimum_mastery_percentage",
                )
            },
        ),
        ("Time Estimation", {"fields": ("estimated_hours",)}),
        ("Teaching Information", {"fields": ("teacher_guide",)}),
    )
