import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django_elasticsearch_dsl.registries import registry

from .models import SubTopic, Topic

log = logging.getLogger(__name__)


@receiver(post_save, sender=SubTopic)
def update_subtopic_document(sender, instance, **kwargs):
    try:
        log.info(
            "Updating SubTopic document",
            extra={
                "subtopic_id": instance.id,
                "subtopic_title": instance.name,
                "action": "update",
            },
        )
        topic = instance.topic
        if topic:
            log.debug(
                "Updating associated Topic document",
                extra={"topic_id": topic.id, "topic_name": topic.name},
            )
            registry.update(topic, raise_on_error=False)
        else:
            log.warning(
                "SubTopic has no associated topic", extra={"subtopic_id": instance.id}
            )
    except Exception as e:
        log.error(
            "Error syncing course structure",
            extra={"subtopic_id": instance.id, "error": str(e)},
            exc_info=True,
        )


@receiver(post_save, sender=Topic)
def update_topic_document(sender, instance, **kwargs):
    try:
        log.info(
            "Updating Topic document",
            extra={
                "topic_id": instance.id,
                "topic_name": instance.name,
                "action": "update",
            },
        )
        registry.update(instance, raise_on_error=False)
    except Exception as e:
        log.error(
            "Error syncing course structure",
            extra={"topic_id": instance.id, "error": str(e)},
            exc_info=True,
        )


@receiver(post_delete, sender=SubTopic)
def delete_subtopic_document(sender, instance, **kwargs):
    try:
        log.info(
            "Deleting SubTopic document",
            extra={
                "subtopic_id": instance.id,
                "subtopic_title": instance.name,
                "action": "delete",
            },
        )

        topic = instance.topic
        if topic:
            log.debug(
                "Updating associated Topic document after SubTopic deletion",
                extra={"topic_id": topic.id, "topic_name": topic.name},
            )
            registry.update(topic, raise_on_error=False)
        else:
            log.warning(
                "Deleted SubTopic had no associated topic",
                extra={"subtopic_id": instance.id},
            )
    except Exception as e:
        log.error(
            "Error syncing course structure",
            extra={"subtopic_id": instance.id, "error": str(e)},
            exc_info=True,
        )


@receiver(post_delete, sender=Topic)
def delete_topic_document(sender, instance, **kwargs):
    try:
        log.info(
            "Deleting Topic document",
            extra={
                "topic_id": instance.id,
                "topic_name": instance.name,
                "action": "delete",
            },
        )
        registry.delete(instance, raise_on_error=False)
    except Exception as e:
        log.error(
            "Error syncing course structure",
            extra={"topic_id": instance.id, "error": str(e)},
            exc_info=True,
        )
