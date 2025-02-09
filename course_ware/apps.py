from django.apps import AppConfig


class CourseWareConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "course_ware"

    def ready(self):
        import course_ware.signals
