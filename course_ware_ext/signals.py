import logging
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist

from course_ware.models import Topic
from course_ware_ext.models import CategoryExt

logger = logging.getLogger(__name__)

POINTS_PER_TOPIC = 100


def update_category_points(category, action="update"):
    """
    Helper function to update category mastery points.

    Args:
        category (Category): Category instance to update
        action (str): Action being performed ("update" or "delete")

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with transaction.atomic():
            category_ext_instance, _ = CategoryExt.objects.get_or_create(category=category)
            total_topics = Topic.objects.filter(category=category).count()
            total_points = total_topics * POINTS_PER_TOPIC
            category_ext_instance.base_mastery_points = total_points
            category_ext_instance.save()

            logger.info(
                f"Successfully updated category points for category_id={category.id}. "
                f"Action: {action}, Total topics: {total_topics}, New points: {total_points}"
            )
            return True

    except Exception as e:
        logger.error(
            f"Failed to update category points for category_id={category.id}. "
            f"Action: {action}, Error: {str(e)}, "
            f"Error type: {type(e).__name__}"
        )
        return False


@receiver(post_save, sender=Topic)
def handle_topic_post_save(sender, instance, created, **kwargs):
    """
    Signal handler triggered after a Topic instance is saved.

    Args:
        sender (Model): The model class sending the signal
        instance (Topic): The Topic instance being saved
        created (bool): Whether this is a new instance
        **kwargs: Additional keyword arguments
    """
    try:
        if not created:
            return

        # Refresh the instance to ensure we have the latest data
        instance.refresh_from_db()

        if not instance.category:
            logger.error(f"Topic ID {instance.id} has no associated category")
            return

        success = update_category_points(instance.category, "create")
        if not success:
            logger.error(f"Failed to process post_save for topic_id={instance.id}")

    except ObjectDoesNotExist as e:
        logger.error(
            f"Topic or related object not found. Topic ID: {instance.id}, Error: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error in topic post_save handler. "
            f"Topic ID: {instance.id}, "
            f"Error type: {type(e).__name__}, "
            f"Error: {str(e)}"
        )


@receiver(post_delete, sender=Topic)
def handle_topic_post_delete(sender, instance, **kwargs):
    """
    Signal handler triggered after a Topic instance is deleted.

    Args:
        sender (Model): The model class sending the signal
        instance (Topic): The Topic instance being deleted
        **kwargs: Additional keyword arguments
    """
    try:
        if not instance.category:
            logger.error(f"Deleted topic has no associated category")
            return

        success = update_category_points(instance.category, "delete")
        if not success:
            logger.error(f"Failed to process post_delete for topic category={instance.category.id}")

    except ObjectDoesNotExist as e:
        logger.error(
            f"Category or related object not found during topic deletion. Error: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error in topic post_delete handler. "
            f"Error type: {type(e).__name__}, "
            f"Error: {str(e)}"
        )