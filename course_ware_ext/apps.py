from django.apps import AppConfig


class CourseWareExtConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "course_ware_ext"

    def ready(self):
        pass
