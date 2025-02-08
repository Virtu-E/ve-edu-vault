from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from course_ware.models import Category, Topic
from course_ware_ext.models import CategoryExt
from elastic_search.tasks import elastic_search_delete_index


@receiver(post_save, sender=Topic)
def handle_topic_post_save(sender, instance, created, **kwargs):
    """
    Signal handler triggered after a Topic instance is saved.

    If a new Topic instance is created, this function:
    - Prints a message indicating the creation of the new topic.
    - Recalculates the base mastery points for the category the topic belongs to.
    - Assigns 100 points per topic in the category.

    Args:
        sender (Model): The model class sending the signal.
        instance (Topic): The specific instance of the Topic model being saved.
        created (bool): A boolean indicating whether a new instance was created.
        **kwargs: Additional keyword arguments.
    """
    if created:
        instance = Topic.objects.get(pk=instance.pk)

        category = instance.category
        category_ext_instance, _ = CategoryExt.objects.get_or_create(category=category)
        total_topics = Topic.objects.filter(category=category).count()
        total_points = total_topics * 100
        category_ext_instance.base_mastery_points = total_points
        category_ext_instance.save()


@receiver(post_delete, sender=Topic)
def handle_topic_post_delete(sender, instance, **kwargs):
    """
    Signal handler triggered after a Topic instance is deleted.

    This function:
    - Recalculates the base mastery points for the category the topic belonged to.
    - Deducts 100 points per deleted topic from the category's total mastery points.

    Args:
        sender (Model): The model class sending the signal.
        instance (Topic): The specific instance of the Topic model being deleted.
        **kwargs: Additional keyword arguments.
    """
    elastic_search_delete_index.delay(instance.block_id)
    category = instance.category
    category_ext_instance, _ = CategoryExt.objects.update_or_create(category=category)
    # Deduct 100 points for the deleted topic
    total_topics = Topic.objects.filter(category=category).count()
    total_points = total_topics * 100
    category_ext_instance.base_mastery_points = total_points
    category_ext_instance.save()


@receiver(post_delete, sender=Category)
def handle_category_post_delete(sender, instance, **kwargs):
    """
    Signal handler triggered after a Category instance is deleted.
    """
    elastic_search_delete_index.delay(instance.block_id)
