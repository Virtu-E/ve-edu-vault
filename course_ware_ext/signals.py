from django.db.models.signals import post_save
from django.dispatch import receiver

from course_ware.models import Topic
from course_ware_ext.models import CategoryExt


@receiver(post_save, sender=Topic)
def handle_post_save(sender, instance, created, **kwargs):
    if created:
        # This block runs only when a new instance is created
        print(f"New {instance} was created")
        # re-calculate the category mastery here
        # each category will be worth about 100 points
        category = instance.category
        category_ext_instance, _ = CategoryExt.objects.update_or_create(
            category=category
        )
        # calculate he mastery points for the category
        # every category will have 100 points attached to it
        total_topics = Topic.objects.filter(category=category_ext_instance).count()
        total_category_pts = total_topics * 100
