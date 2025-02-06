import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from django.db.models import Model

from course_ware.models import DefaultQuestionSet, Topic, TopicIframeID
from edu_vault.settings import common
from no_sql_database.nosql_database_engine import NoSqLDatabaseEngineInterface
from webhooks.edx_requests import EdxClient

log = logging.getLogger(__name__)


# TODO : clean this file. Create separate files for individual logic flow
class CreationSideEffect(ABC):
    """Abstract base class for creation side effects."""

    @abstractmethod
    def process_creation_side_effects(self, instance: Model) -> None:
        raise NotImplementedError


def get_first_lti_consumer_id(course_blocks: Dict[str, Any]) -> str | None:
    """
    Get the first LTI consumer block ID from the course blocks data structure.

    Args:
        course_blocks (dict): Course blocks data with root and blocks information

    Returns:
        str: First LTI consumer block ID if found, None otherwise
    """
    blocks = course_blocks.get("blocks", {})

    for block_id, block_data in blocks.items():
        if block_data.get("type") == "lti_consumer":
            return block_id

    return None


def normalize_name(name: str) -> str:
    """
    Normalize a name by converting to lowercase and replacing spaces with underscores.

    Args:
        name (str): The name to normalize

    Returns:
        str: Normalized name
    """
    return name.lower().replace(" ", "_").lstrip("_")


def create_aggregation_pipeline(topic: Topic) -> List[Dict[str, Any]]:
    """
    Create the MongoDB aggregation pipeline for retrieving questions.

    Args:
        topic (Topic): The topic instance

    Returns:
        List[Dict[str, Any]]: Aggregation pipeline
    """
    normalized_topic_name = normalize_name(topic.name)
    normalized_category_name = normalize_name(topic.category.name)

    return [
        {
            "$match": {
                "academic_class": topic.category.academic_class.name,
                "examination_level": topic.category.examination_level.name,
                "category": normalized_category_name,
                "topic": normalized_topic_name,
            }
        },
        {
            "$facet": {
                "easy": [
                    {"$match": {"difficulty": "easy"}},
                    {"$sample": {"size": 3}},
                ],
                "medium": [
                    {"$match": {"difficulty": "medium"}},
                    {"$sample": {"size": 3}},
                ],
                "hard": [
                    {"$match": {"difficulty": "hard"}},
                    {"$sample": {"size": 3}},
                ],
            }
        },
    ]


def get_question_list_ids(results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Extract question IDs from aggregation results.

    Args:
        results (List[Dict[str, Any]]): Aggregation results

    Returns:
        List[Dict[str, str]]: List of question IDs
    """
    question_list_ids = []
    for difficulty_level in ["easy", "medium", "hard"]:
        question_list_ids.extend({"id": str(question["_id"])} for question in results[0].get(difficulty_level, []))
    return question_list_ids


def create_default_question_set(topic: Topic, question_list_ids: List[Dict[str, str]]) -> None:
    """
    Create or update the DefaultQuestionSet for a topic.

    Args:
        topic (Topic): The topic instance
        question_list_ids (List[Dict[str, str]]): List of question IDs
    """
    DefaultQuestionSet.objects.update_or_create(topic=topic, defaults={"question_list_ids": question_list_ids})


def create_topic_iframe_id(topic: Topic, course_blocks: Dict[str, Any]) -> None:
    """
    Create or update the TopicIframeID if LTI consumer is configured.

    Args:
        topic (Topic): The topic instance
        course_blocks (Dict[str, Any]): Course blocks data
    """
    if course_blocks:
        iframe_id = get_first_lti_consumer_id(course_blocks)
        if iframe_id:
            TopicIframeID.objects.update_or_create(topic=topic, defaults={"identifier": iframe_id})


class TopicCreationSideEffect(CreationSideEffect):
    """Class to handle all related creation side effects in relation to a topic instance."""

    def __init__(self, no_sql_database_client: NoSqLDatabaseEngineInterface) -> None:
        self.no_sql_database_client = no_sql_database_client

    # TODO : this can be made  better
    @staticmethod
    def _get_edx_client():
        return EdxClient("OPENEDX")

    def process_creation_side_effects(self, topic: Topic) -> None:
        """
        Process all side effects related to topic creation.

        Args:
            topic (Topic): The topic instance
        """
        try:
            pipeline = create_aggregation_pipeline(topic)

            results = self.no_sql_database_client.run_aggregation(
                collection_name=topic.category.course.course_key,
                database_name=getattr(common, "NO_SQL_DATABASE_NAME", "virtu_educate"),
                pipeline=pipeline,
            )

            question_list_ids = get_question_list_ids(results)
            create_default_question_set(topic, question_list_ids)

            course_blocks = self._get_edx_client().get_course_blocks(topic.block_id)
            create_topic_iframe_id(topic, course_blocks)

        except Exception as e:
            log.exception(f"Failed to create topic creation side effect due to: {e}")
