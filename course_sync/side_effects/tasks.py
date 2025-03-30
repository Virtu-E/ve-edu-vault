import logging

from celery import shared_task

from course_sync.side_effects.topic_creation_side_effect import TopicCreationSideEffect
from course_ware.models import Topic
from edu_vault.settings.common import MONGO_URL
from oauth_clients.edx_client import EdxClient

log = logging.getLogger(__name__)


@shared_task(
    name="course_sync.tasks.topic_creation_side_effect",
    ignore_result=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_topic_creation_side_effect(topic: int):
    try:
        topic = Topic.objects.get(pk=topic)
        mongo = MongoDatabaseEngine(MONGO_URL)
        client = EdxClient("OPENEDX")
        side_effect = TopicCreationSideEffect(
            no_sql_database_client=mongo, client=client, topic=topic
        )
        side_effect.process_creation_side_effects()
    except Exception as e:
        log.error(
            f"Failed to process topic creation side effects for topic ID {topic.id}. "
            f"Error type: {type(e).__name__}. "
            f"Details: {str(e)}. "
            # f"Retry attempt {task.request.retries + 1} of {task.max_retries}"
        )
        # raise task.retry(exc=e)
