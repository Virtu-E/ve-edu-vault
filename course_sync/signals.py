import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from course_sync.side_effects.tasks import process_topic_creation_side_effect
from course_ware.models import Topic

log = logging.getLogger(__name__)


@receiver(post_save, sender=Topic)
def trigger_topic_side_effect(sender, instance, **kwargs):
    """
    Signal receiver to handle topic creation side effects.

    Args:
        sender: The model class (Topic)
        instance: The actual Topic instance being saved
        kwargs: Additional keyword arguments including 'created' flag
    """
    if kwargs.get("created"):
        log.info(
            "New Topic created - triggering side effects",
            extra={
                "topic_id": instance.id,
                "topic_name": instance.name,
            },
        )
        try:
            pk = instance.id
            process_topic_creation_side_effect.delay(pk)
            log.debug(
                f"Successfully queued topic creation side effect task for topic ID: {instance.id}"
            )
        except Exception as e:
            log.error(
                "Failed to queue topic creation side effect task",
                exc_info=True,
                extra={"topic_id": instance.id, "error": str(e)},
            )
