# Generated by Django 5.2 on 2025-05-22 15:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("webhooks", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(
            name="SucceededEvents",
        ),
    ]
