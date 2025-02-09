import logging
from typing import Any, Dict

from celery import shared_task

from elastic_search.operations import ElasticSearchHandler
from elastic_search.task_manager import ElasticTaskManager

ES_HANDLER = ElasticSearchHandler

log = logging.getLogger(__name__)


# @shared_task(name="tasks.elastic_search_sync", max_retries=3, default_retry_delay=60)
# def elastic_search_sync(result: Dict[str, Any]) -> None:
#     """Second task in chain: Sync with Elasticsearch"""
#     if result.get("status") != "success":
#         raise ValueError(f"Course update failed: {result.get('message')}")
#
#     if not result.get("changes_made"):
#         log.info("No changes made, not syncing course to elasticsearch")
#
#     course_id = result["course_id"]
#
#     try:
#         ElasticTaskManager(ES_HANDLER).sync_course(course_id)
#         log.info(f"Course and Elasticsearch sync completed for {course_id}")
#
#     except Exception as e:
#         raise ValueError(f"Elasticsearch sync failed: {str(e)}")


# @shared_task(name="tasks.elastic_delete_index", max_retries=3, default_retry_delay=60)
# def elastic_search_delete_index(index_id: str) -> None:
#     """Celery task to delete an Elasticsearch index"""
#     ElasticTaskManager(ES_HANDLER).delete_index(index_id)
