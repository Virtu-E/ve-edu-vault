import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django_elasticsearch_dsl.registries import registry

from .models import Category, Topic

log = logging.getLogger(__name__)


@receiver(post_save, sender=Topic)
def update_topic_document(sender, instance, **kwargs):
    try:
        log.info(
            "Updating Topic document",
            extra={
                "topic_id": instance.id,
                "topic_title": instance.name,
                "action": "update",
            },
        )
        category = instance.category
        if category:
            log.debug(
                "Updating associated Category document",
                extra={"category_id": category.id, "category_name": category.name},
            )
            registry.update(category, raise_on_error=False)
        else:
            log.warning("Topic has no associated category", extra={"topic_id": instance.id})
    except Exception as e:
        log.error(
            "Error syncing course structure",
            extra={
                "topic_id": instance.id,
                "error": str(e)
            },
            exc_info=True
        )


@receiver(post_save, sender=Category)
def update_category_document(sender, instance, **kwargs):
    try:
        log.info(
            "Updating Category document",
            extra={
                "category_id": instance.id,
                "category_name": instance.name,
                "action": "update",
            },
        )
        registry.update(instance, raise_on_error=False)
    except Exception as e:
        log.error(
            "Error syncing course structure",
            extra={
                "category_id": instance.id,
                "error": str(e)
            },
            exc_info=True
        )


@receiver(post_delete, sender=Topic)
def delete_topic_document(sender, instance, **kwargs):
    try:
        log.info(
            "Deleting Topic document",
            extra={
                "topic_id": instance.id,
                "topic_title": instance.name,
                "action": "delete",
            },
        )

        category = instance.category
        if category:
            log.debug(
                "Updating associated Category document after Topic deletion",
                extra={"category_id": category.id, "category_name": category.name},
            )
            registry.update(category, raise_on_error=False)
        else:
            log.warning(
                "Deleted Topic had no associated category",
                extra={"topic_id": instance.id}
            )
    except Exception as e:
        log.error(
            "Error syncing course structure",
            extra={
                "topic_id": instance.id,
                "error": str(e)
            },
            exc_info=True
        )


@receiver(post_delete, sender=Category)
def delete_category_document(sender, instance, **kwargs):
    try:
        log.info(
            "Deleting Category document",
            extra={
                "category_id": instance.id,
                "category_name": instance.name,
                "action": "delete",
            },
        )
        registry.delete(instance,raise_on_error=False)
    except Exception as e:
        log.error(
            "Error syncing course structure",
            extra={
                "category_id": instance.id,
                "error": str(e)
            },
            exc_info=True
        )