from typing import Any, Dict, List

from ai_core.learning_mode_rules import LearningModeType
from ai_core.orchestration.tasks import process_orchestration
from data_types.ai_core import PerformanceStats
from data_types.course_ware_schema import QuestionMetadata


def trigger_orchestration(
    block_id: str,
    user_id: int,
    question_metadata: Dict[str, QuestionMetadata | Any],
    question_list_ids: List[str],
    course_id: int,
    topic_id: int,
    category_id: int,
    learning_mode: LearningModeType,
    performance_stats: PerformanceStats,
):
    """
    Triggers the orchestration process asynchronously.
    """
    # Convert PerformanceStats to dict
    performance_stats_data = performance_stats.model_dump()

    # Convert QuestionMetadata objects to dicts where needed
    serializable_metadata = {
        key: value.model_dump() if isinstance(value, QuestionMetadata) else value
        for key, value in question_metadata.items()
    }

    # This returns an AsyncResult object
    task = process_orchestration(
        block_id=block_id,
        user_id=user_id,
        question_metadata=serializable_metadata,
        question_list_ids=question_list_ids,
        course_id=course_id,
        topic_id=topic_id,
        category_id=category_id,
        learning_mode=learning_mode,
        performance_stats_data=performance_stats_data,
    )

    return task


# task = process_orchestration.apply_async(
#       kwargs={
#           "block_id": block_id,
#           "user_id": user_id,
#           "question_metadata": serializable_metadata,
#           "question_list_ids": question_list_ids,
#           "course_id": course_id,
#           "topic_id": topic_id,
#           "category_id": category_id,
#           "learning_mode": learning_mode,
#           "performance_stats_data": performance_stats_data,
#       }
#   )
