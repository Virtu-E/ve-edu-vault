from django.apps import apps
from django.contrib import admin

# Get all models from the app
app = apps.get_app_config("course_ware")

# Loop through all models and register them
for model in app.models.values():
    admin.site.register(model)
