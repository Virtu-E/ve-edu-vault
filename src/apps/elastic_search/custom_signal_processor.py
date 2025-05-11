import logging
from importlib import import_module

from celery import shared_task
from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl.signals import CelerySignalProcessor

from src.apps.core.content.models import SubTopic, Topic

log = logging.getLogger(__name__)


class CustomCelerySignalProcessor(CelerySignalProcessor):
    """Custom Celery signal processor with error handling."""

    def handle_save(self, sender, instance, **kwargs):
        """Handle save with a Celery task and error handling."""

        if not isinstance(instance, (SubTopic, Topic)):
            return  # Skip if not one of our target models

        pk = instance.pk
        app_label = instance._meta.app_label
        model_name = instance.__class__.__name__

        self.registry_update_task.delay(pk, app_label, model_name)
        self.registry_update_related_task.delay(pk, app_label, model_name)

    def handle_pre_delete(self, sender, instance, **kwargs):
        """Handle pre-delete with error handling."""
        if not isinstance(instance, (SubTopic, Topic)):
            return  # Skip if not one of our target models

        try:
            self.prepare_registry_delete_related_task(instance)
        except Exception as e:
            log.error(
                "Error in pre-delete handling for Elasticsearch",
                extra={
                    "model": sender.__name__,
                    "instance_id": instance.id,
                    "error": str(e),
                },
                exc_info=True,
            )

    def handle_delete(self, sender, instance, **kwargs):
        """Handle delete with error handling."""
        if not isinstance(instance, (SubTopic, Topic)):
            return  # Skip if not one of our target models
        try:
            self.prepare_registry_delete_task(instance)
        except Exception as e:
            log.error(
                "Error handling delete for Elasticsearch",
                extra={
                    "model": sender.__name__,
                    "instance_id": instance.id,
                    "error": str(e),
                },
                exc_info=True,
            )

    def prepare_registry_delete_related_task(self, instance):
        """Prepare registry delete related task with error handling."""

        action = "index"
        for doc in registry._get_related_doc(instance):
            try:
                doc_instance = doc(related_instance_to_ignore=instance)
                try:
                    related = doc_instance.get_instances_from_related(instance)
                except ObjectDoesNotExist:
                    log.warning(
                        "Related object does not exist",
                        extra={"instance_id": instance.id, "doc_class": doc.__name__},
                    )
                    related = None

                if related is not None:
                    doc_instance.update(related)
                    if isinstance(related, models.Model):
                        object_list = [related]
                    else:
                        object_list = related
                    bulk_data = (list(doc_instance._get_actions(object_list, action)),)
                    self.registry_delete_task.delay(
                        doc_instance.__class__.__name__, bulk_data
                    )
            except Exception as e:
                log.error(
                    "Error preparing registry delete related task",
                    extra={
                        "instance_id": instance.id,
                        "doc_class": doc.__name__,
                        "error": str(e),
                    },
                    exc_info=True,
                )

    @shared_task()
    def registry_delete_task(doc_label, data):
        """Handle the bulk delete with error handling."""
        try:
            doc_instance = import_module(doc_label)
            parallel = True
            doc_instance._bulk(bulk_data, parallel=parallel)  # noqa
        except Exception as e:
            log.error(
                "Error in registry delete task",
                extra={"doc_label": doc_label, "error": str(e)},
                exc_info=True,
            )

    def prepare_registry_delete_task(self, instance):
        """Prepare registry delete task with error handling."""
        action = "delete"
        for doc in registry._get_related_doc(instance):
            try:
                doc_instance = doc(related_instance_to_ignore=instance)
                try:
                    related = doc_instance.get_instances_from_related(instance)
                except ObjectDoesNotExist:
                    log.warning(
                        "Related object does not exist for delete",
                        extra={"instance_id": instance.id, "doc_class": doc.__name__},
                    )
                    related = None

                if related is not None:
                    doc_instance.update(related)
                    if isinstance(related, models.Model):
                        object_list = [related]
                    else:
                        object_list = related
                    bulk_data = (list(doc_instance.get_actions(object_list, action)),)
                    self.registry_delete_task.delay(
                        doc_instance.__class__.__name__, bulk_data
                    )
            except Exception as e:
                log.error(
                    "Error preparing registry delete task",
                    extra={
                        "instance_id": instance.id,
                        "doc_class": doc.__name__,
                        "error": str(e),
                    },
                    exc_info=True,
                )

    @shared_task()
    def registry_update_task(pk, app_label, model_name):
        """Handle the update task with error handling."""
        try:
            model = apps.get_model(app_label, model_name)
            instance = model.objects.get(pk=pk)
            registry.update(instance)
        except LookupError:
            log.info(
                f"Model {app_label}.{model_name} not found",
                extra={"pk": pk, "app_label": app_label, "model_name": model_name},
            )
        except ObjectDoesNotExist:
            log.info(
                f"{model_name} matching query does not exist",
                extra={"pk": pk, "app_label": app_label, "model_name": model_name},
            )

    @shared_task()
    def registry_update_related_task(pk, app_label, model_name):
        """Handle the related update task with error handling."""
        try:
            model = apps.get_model(app_label, model_name)
            instance = model.objects.get(pk=pk)
            registry.update_related(instance)
        except LookupError:
            log.info(
                f"Model {app_label}.{model_name} not found for related update",
                extra={"pk": pk, "app_label": app_label, "model_name": model_name},
            )
        except ObjectDoesNotExist:
            log.info(
                f"{model_name} matching query does not exist for related update",
                extra={"pk": pk, "app_label": app_label, "model_name": model_name},
            )
