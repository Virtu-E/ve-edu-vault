from django.contrib import admin

# Register your models here.


@admin.register(UserAssessmentAttempt)
class UserAssessmentAttemptAdmin(JsonWidgetModelAdmin):
    list_display = [
        "user",
        "learning_objective",
    ]
    search_fields = ["user__username", "learning_objective__name"]
    raw_id_fields = ["user", "learning_objective"]
