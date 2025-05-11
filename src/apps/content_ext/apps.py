from django.apps import AppConfig


class CourseWareExtConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "src.apps.content_ext"

    def ready(self):
        pass
