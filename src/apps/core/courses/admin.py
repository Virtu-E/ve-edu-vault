from django.contrib import admin


# Register your models here.
@admin.register(Course)
class CourseAdmin(JsonWidgetModelAdmin):
    list_display = ["name", "course_key", "view_topics"]
    search_fields = ["name", "course_key"]

    def view_topics(self, obj):
        url = reverse("admin:course_ware_topic_changelist") + f"?course__id={obj.id}"
        return format_html('<a href="{}">View Topics</a>', url)

    view_topics.short_description = "Topics"


@admin.register(AcademicClass)
class AcademicClassAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


admin.site.register(ExaminationLevel)
