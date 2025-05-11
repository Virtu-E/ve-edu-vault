from django.contrib import admin

from .models import EdxUser


# Register your models here.


@admin.register(EdxUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "email", "active"]
    search_fields = ["username", "email"]
    list_filter = ["active"]
