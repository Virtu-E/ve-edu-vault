import logging
from abc import ABC, abstractmethod

from django.db.models import Model

from course_ware.models import DefaultQuestionSet, Topic
from edu_vault.settings import common
from no_sql_database.nosql_database_engine import NoSqLDatabaseEngineInterface

log = logging.getLogger(__name__)


class CreationSideEffect(ABC):
    """Abstract base class for creation side effects."""

    @abstractmethod
    def process_creation_side_effects(self, instance: Model) -> None:
        raise NotImplementedError


class TopicCreationSideEffect(CreationSideEffect):
    """Class to handle all related creation side effects in relation to a topic instance."""

    def __init__(self, no_sql_database_client: NoSqLDatabaseEngineInterface) -> None:
        self.no_sql_database_client = no_sql_database_client

    def process_creation_side_effects(self, topic: Topic) -> None:

        normalized_topic_name = topic.name.lower().replace(" ", "_").lstrip("_")
        normalized_category_name = (
            topic.category.name.lower().replace(" ", "_").lstrip("_")
        )

        log.info(
            {
                "academic_class": topic.category.academic_class.name,
                "examination_level": topic.category.examination_level,
                "category": normalized_category_name,
                "topic": normalized_topic_name,
            }
        )

        #
        # {
        #     "academic_class": "Form 1",
        #     "examination_level": "JCE",
        #     "category": "introduction_to_chemistry",
        #     "topic": "meaning_of_chemistry",
        # }

        pipeline = [
            {
                "$match": {
                    "academic_class": topic.category.academic_class.name,
                    "examination_level": topic.category.examination_level,
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
        try:
            # Run the aggregation pipeline
            results = self.no_sql_database_client.run_aggregation(
                collection_name=topic.category.course.course_key,
                database_name=getattr(common, "NO_SQL_DATABASE_NAME", "virtu_educate"),
                pipeline=pipeline,
            )

            # Flatten the results to get all question IDs
            question_list_ids = []
            for difficulty_level in ["easy", "medium", "hard"]:
                question_list_ids.extend(
                    {"id": str(question["_id"])}
                    for question in results[0].get(difficulty_level, [])
                )

            # Create the DefaultQuestionSet instance
            DefaultQuestionSet.objects.update_or_create(
                topic=topic, defaults={"question_list_ids": question_list_ids}
            )
            log.info(question_list_ids)

        except Exception as e:
            log.exception(
                "Failed to create topic creation side effect due to: {}".format(e)
            )
