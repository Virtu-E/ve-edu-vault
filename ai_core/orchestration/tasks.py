import logging

from celery import shared_task

from ai_core.learning_mode_rules import LearningModeType, LearningRuleFactory
from ai_core.orchestration.orchestration_engine import OrchestrationEngine
from data_types.ai_core import PerformanceStats
from data_types.course_ware_schema import QuestionMetadata
from edu_vault.settings.common import MONGO_URL
from repository.databases.no_sql_database import MongoDatabaseEngine

log = logging.getLogger(__name__)


@shared_task(name="tasks.process_orchestration", max_retries=3, default_retry_delay=60)
def process_orchestration(**kwargs):
    """Process orchestration engine data asynchronously."""
    try:
        mongo = MongoDatabaseEngine(MONGO_URL)
        orchestration_engine = OrchestrationEngine(
            block_id=kwargs["block_id"],
            user_id=kwargs["user_id"],
            question_metadata={
                key: (
                    QuestionMetadata(**value).model_dump()
                    if isinstance(value, dict)
                    else value
                )
                for key, value in kwargs["question_metadata"].items()
            },
            question_set_ids=set(kwargs["question_list_ids"]),
            course_id=kwargs["course_id"],
            topic_id=kwargs["topic_id"],
            category_id=kwargs["category_id"],
            learning_mode=LearningModeType.from_string(kwargs["learning_mode"]),
            learning_mode_rule=LearningRuleFactory.create_rule(
                LearningModeType.from_string(kwargs["learning_mode"])
            ),
            performance_stats=PerformanceStats(**kwargs["performance_stats_data"]),
            database_engine=mongo,
        )
        results = orchestration_engine.process_question()
        log.info(results)

        return results
    except Exception as e:
        log.error(f"Error processing orchestration: {str(e)}")
        raise
    finally:
        mongo.disconnect()
