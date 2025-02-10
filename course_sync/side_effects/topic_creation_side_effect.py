import logging
from typing import Any, Dict, List, Optional

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from course_sync.side_effects.abstract_type import CreationSideEffect
from course_ware.models import DefaultQuestionSet, Topic, TopicIframeID
from edu_vault.settings import common
from no_sql_database.nosql_database_engine import NoSqLDatabaseEngineInterface
from oauth_clients.edx_client import EdxClient

log = logging.getLogger(__name__)


class TopicCreationSideEffect(CreationSideEffect):
    """Class to handle all related creation side effects in relation to a topic instance."""

    def __init__(
        self,
        no_sql_database_client: NoSqLDatabaseEngineInterface,
        client: EdxClient,
        topic: Topic,
    ) -> None:
        """
        Initialize the TopicCreationSideEffect.

        Args:
            no_sql_database_client: Database client for NoSQL operations
            client: EdX client for course operations
            topic: Topic instance to process
        """
        self.no_sql_database_client = no_sql_database_client
        self._client = client

        # Refresh topic instance to ensure we have latest data
        try:
            topic.refresh_from_db()
            self._topic = topic
        except ObjectDoesNotExist:
            log.error(f"Topic with ID {topic.id} not found during initialization")
            raise

        log.info(
            f"Initialized TopicCreationSideEffect for topic: {topic.name} (ID: {topic.id})"
        )

    def process_creation_side_effects(self) -> None:
        """Process all side effects related to topic creation."""
        try:
            # Refresh related objects to ensure we have latest data

            log.info(f"Starting creation side effects for topic: {self._topic.name}")

            if not self._topic.category or not self._topic.category.course:
                raise ValueError("Topic must have associated category and course")

            with transaction.atomic():
                pipeline = self._create_aggregation_pipeline()

                log.info(
                    f"Running aggregation for course key: {self._topic.category.course.course_key}"
                )
                results = self.no_sql_database_client.run_aggregation(
                    collection_name=self._topic.category.course.course_key,
                    database_name=getattr(
                        common, "NO_SQL_DATABASE_NAME", "virtu_educate"
                    ),
                    pipeline=pipeline,
                )

                question_list_ids = self._get_question_list_ids(results)

                log.debug("Creating default question set")
                self._create_default_question_set(question_list_ids)

                log.info(f"Fetching course blocks for block ID: {self._topic.block_id}")
                course_blocks = self._client.get_course_blocks(self._topic.block_id)

                self._create_topic_iframe_id(course_blocks)

            # Refresh topic one final time to ensure consistency
            self._topic.refresh_from_db()

            log.info(
                f"Successfully completed all creation side effects for topic: {self._topic.name}"
            )

        except ObjectDoesNotExist as e:
            log.error(
                f"Required object not found while processing topic {self._topic.id}",
                exc_info=True,
                extra={"topic_id": self._topic.id, "error": str(e)},
            )
            raise
        except Exception as e:
            log.error(
                f"Failed to create topic creation side effect for topic {self._topic.name}",
                exc_info=True,
                extra={
                    "topic_id": self._topic.id,
                    "category": getattr(self._topic.category, "name", None),
                    "course_key": getattr(
                        getattr(self._topic.category, "course", None),
                        "course_key",
                        None,
                    ),
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
            )
            raise

    def _create_default_question_set(
        self, question_list_ids: List[Dict[str, str]]
    ) -> None:
        """
        Create or update the DefaultQuestionSet for a topic.

        Args:
            question_list_ids: List of question IDs
        """
        log.info(
            f"Creating/updating DefaultQuestionSet for topic {self._topic.name} with {len(question_list_ids)} questions"
        )
        try:
            with transaction.atomic():
                self._topic.refresh_from_db()  # Ensure we have latest topic data
                DefaultQuestionSet.objects.update_or_create(
                    topic=self._topic, defaults={"question_list_ids": question_list_ids}
                )
        except Exception:
            log.error(
                f"Failed to create/update DefaultQuestionSet for topic {self._topic.id}",
                exc_info=True,
                extra={"question_count": len(question_list_ids)},
            )
            raise

    def _create_topic_iframe_id(self, course_blocks: Dict[str, Any]) -> None:
        """
        Create or update the TopicIframeID if LTI consumer is configured.

        Args:
            course_blocks: Course blocks data
        """
        try:
            with transaction.atomic():
                self._topic.refresh_from_db()  # Ensure we have latest topic data
                if course_blocks:
                    iframe_id = self._get_first_lti_consumer_id(course_blocks)
                    if iframe_id:
                        TopicIframeID.objects.update_or_create(
                            topic=self._topic, defaults={"identifier": iframe_id}
                        )
                    else:
                        log.warning(f"No iframe ID found for topic {self._topic.name}")
                else:
                    log.warning(
                        f"No course blocks available for topic {self._topic.name}"
                    )
        except Exception:
            log.error(
                f"Failed to create/update TopicIframeID for topic {self._topic.id}",
                exc_info=True,
                extra={"course_blocks_available": bool(course_blocks)},
            )
            raise

    @staticmethod
    def _get_first_lti_consumer_id(course_blocks: Dict[str, Any]) -> Optional[str]:
        """
        Get the first LTI consumer block ID from the course blocks data structure.

        Args:
            course_blocks: Course blocks data with root and blocks information

        Returns:
            First LTI consumer block ID if found, None otherwise
        """
        blocks = course_blocks.get("blocks", {})

        for block_id, block_data in blocks.items():
            if block_data.get("type") == "lti_consumer":
                log.info(f"Found LTI consumer block: {block_id}")
                return block_id

        log.warning("No LTI consumer block found in course blocks")
        return None

    @staticmethod
    def _normalize_name(name: str) -> str:
        """
        Normalize a name by converting to lowercase and replacing spaces with underscores.

        Args:
            name: The name to normalize

        Returns:
            Normalized name
        """
        normalized = name.lower().replace(" ", "_").lstrip("_")
        log.debug(f"Normalized name '{name}' to '{normalized}'")
        return normalized

    @staticmethod
    def _get_question_list_ids(results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Extract question IDs from aggregation results.

        Args:
            results: Aggregation results

        Returns:
            List of question IDs
        """
        question_list_ids = []
        for difficulty_level in ["easy", "medium", "hard"]:
            questions = results[0].get(difficulty_level, [])
            log.debug(
                f"Found {len(questions)} questions for {difficulty_level} difficulty"
            )
            question_list_ids.extend(
                {"id": str(question["_id"])} for question in questions
            )
        return question_list_ids

    def _create_aggregation_pipeline(self) -> List[Dict[str, Any]]:
        """
        Create the MongoDB aggregation pipeline for retrieving questions.

        Returns:
            List[Dict[str, Any]]: Aggregation pipeline
        """
        normalized_topic_name = self._normalize_name(self._topic.name)
        normalized_category_name = self._normalize_name(self._topic.category.name)

        log.debug(
            f"Creating pipeline with normalized names - Topic: {normalized_topic_name}, Category: {normalized_category_name}"
        )

        return [
            {
                "$match": {
                    "academic_class": self._topic.category.academic_class.name,
                    "examination_level": self._topic.category.examination_level.name,
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
