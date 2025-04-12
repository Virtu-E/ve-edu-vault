import logging
from typing import Any, Dict, Iterable, List

from bson import ObjectId, errors

from edu_vault.settings import common

from .data_types import Question
from .databases.no_sql_database.mongodb import _AsyncMongoDatabaseEngine, mongo_database
from .repository_mixin import QuestionRepositoryMixin

log = logging.getLogger(__name__)


class MongoQuestionRepository(QuestionRepositoryMixin):
    """
    Repository class for retrieving Question objects from MongoDB.

    Attributes:
        database_engine: An instance of _AsyncMongoDatabaseEngine for database interactions.
        database_name: The name of the database to query.
    """

    def __init__(
        self,
        database_engine: _AsyncMongoDatabaseEngine,
        database_name: str,
    ) -> None:
        """
        Initialize the MongoQuestionRepository.

        Args:
            database_engine: The MongoDB database engine to use for queries.
            database_name: The name of the database to query.
        """
        self.database_engine = database_engine
        self.database_name = database_name

    @staticmethod
    def _validate_question_ids(question_ids: List[str]) -> List[ObjectId]:
        """
        Validate and convert string IDs to MongoDB ObjectId instances.

        Args:
            question_ids: List of string IDs to validate and convert.

        Returns:
            List of valid MongoDB ObjectId instances.
        """
        object_ids = []
        for id_ in question_ids:
            try:
                if ObjectId.is_valid(id_):
                    object_ids.append(ObjectId(id_))
                else:
                    log.warning("Invalid ObjectId format: %s", id_)
            except errors.InvalidId:
                log.warning("Failed to convert ID to ObjectId: %s", id_)

        if not object_ids:
            log.warning("No valid question IDs to query")
            return []
        return object_ids

    def _process_mongo_question_data(
        self, questions: Iterable[Dict[str, Any]]
    ) -> List[Question]:
        """
        Process raw MongoDB documents into Question domain objects.

        Args:
            questions: Iterable of MongoDB document dictionaries.

        Returns:
            List of Question objects created from the MongoDB documents.
        """
        result = []
        for question in questions:
            try:
                question_with_string_id = {**question, "_id": str(question["_id"])}

                question_obj = Question(**question_with_string_id).model_dump(
                    by_alias=True, exclude={"choices": {"is_correct"}}
                )
                result.append(question_obj)
                # TODO : dont catch all exceptions like that, very bad
            except Exception as e:
                log.error(
                    "Error processing question data: %s. Error: %s",
                    question.get("_id"),
                    str(e),
                )
        return result

    def get_questions_by_ids(
        self, question_ids: List[str], collection_name: str
    ) -> List[Question]:
        """
        Retrieve multiple questions by their IDs from the specified collection.

        Args:
            question_ids: A list of question ID strings to retrieve.
            collection_name: The name of the collection to query.

        Returns:
            A list of Question objects with their data. Returns an empty list
            if no valid question IDs are provided or found.

        Raises:
            ValueError: If collection_name is empty.
        """
        if not collection_name:
            log.error("Empty collection name provided")
            raise ValueError("Collection name cannot be empty")

        if not question_ids:
            log.warning("No question IDs provided to retrieve")
            return []

        object_ids = self._validate_question_ids(question_ids)

        if not object_ids:
            return []

        query = {"_id": {"$in": object_ids}}
        log.debug("Querying collection '%s' with filter: %s", collection_name, query)

        questions = self.database_engine.fetch_from_db(
            collection_name, self.database_name, query
        )

        result = self._process_mongo_question_data(questions)
        log.info(
            "Retrieved %d questions out of %d requested IDs",
            len(result),
            len(question_ids),
        )

        return result

    def get_question_by_single_id(
        self, question_id: str, collection_name: str
    ) -> Question:
        response = self.database_engine.fetch_from_db(
            collection_name, self.database_name, {"_id": ObjectId(question_id)}
        )
        result = response[0] if isinstance(response, list) else response
        return Question(**{**result, "_id": str(question_id)})

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

    async def get_questions_by_aggregation(
        self,
        collection_name: str,
        examination_level: str,
        academic_class: str,
        subtopic_name: str,
        topic_name: str,
    ) -> List[Question]:
        normalized_topic_name = self._normalize_name(subtopic_name)
        normalized_subtopic_name = self._normalize_name(topic_name)

        pipeline = [
            {
                "$match": {
                    "academic_class": academic_class,
                    "examination_level": examination_level,
                    "subtopic": normalized_subtopic_name,
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

        questions = await self.database_engine.run_aggregation(
            collection_name, self.database_name, pipeline
        )

        result = self._process_mongo_question_data(questions)
        return result

    @classmethod
    def get_repo(cls):
        database_name = getattr(common, "NO_SQL_DATABASE_NAME", None)
        if database_name is None:
            # TODO : raise custom error exception here for better details
            raise RuntimeError()
        return MongoQuestionRepository(
            database_engine=mongo_database,
            database_name=database_name,
        )
