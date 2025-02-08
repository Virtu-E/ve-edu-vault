from celery import shared_task

from elastic_search.operations import ElasticSearchHandler
from elastic_search.task_manager import ElasticTaskManager

ES_HANDLER = ElasticSearchHandler


@shared_task(name="tasks.elastic_search_sync", max_retries=3, default_retry_delay=60)
def elastic_search_sync(course_id: str) -> None:
    """Celery task to sync course data with Elasticsearch"""
    ElasticTaskManager(ES_HANDLER).sync_course(course_id)


@shared_task(name="tasks.elastic_delete_index", max_retries=3, default_retry_delay=60)
def elastic_search_delete_index(index_id: str) -> None:
    """Celery task to delete an Elasticsearch index"""
    ElasticTaskManager(ES_HANDLER).delete_index(index_id)
