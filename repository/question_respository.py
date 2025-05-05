import logging
from typing import Any, Dict, Iterable, List

from bson import ObjectId, errors

from edu_vault.settings import common

from .data_types import Question
from .databases.no_sql_database.mongodb import AsyncMongoDatabaseEngine, mongo_database
from .repository_mixin import QuestionRepositoryMixin

log = logging.getLogger(__name__)


class MongoQuestionRepository(QuestionRepositoryMixin):
    """
    Repository class for retrieving Question objects from MongoDB.

    Attributes:
        database_engine: An instance of _AsyncMongoDatabaseEngine for database interactions.
        database_name: The name of the database to query.
    """

    __slots__ = ("database_engine", "database_name")

    def __init__(
        self,
        database_engine: AsyncMongoDatabaseEngine,
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
        log.info(
            "Initialized MongoQuestionRepository with database '%s'", database_name
        )

    async def get_questions_by_ids(
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
        # TODO : write a decorator function for this validation
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

        all_questions = []

        # consuming the generator content for now
        # since they're mostly a few question documents
        async for batch in await self.database_engine.fetch_from_db(
            collection_name, self.database_name, query
        ):
            all_questions.extend(batch)

        result = self._process_mongo_question_data(all_questions)
        log.info(
            "Retrieved %d questions out of %d requested IDs",
            len(result),
            len(question_ids),
        )

        return result

    async def get_question_by_single_id(
        self, question_id: str, collection_name: str
    ) -> Question:
        response = await self.database_engine.fetch_one_from_db(
            collection_name, self.database_name, {"_id": ObjectId(question_id)}
        )
        if not response:
            raise ValueError("Mongo Question with ID '%s' not found" % question_id)

        result = response[0] if isinstance(response, list) else response
        return Question(**{**result, "_id": str(question_id)})

    async def get_questions_by_aggregation(
        self, collection_name: str, pipeline: Any
    ) -> List[Question]:
        """
        Retrieve and process questions using a MongoDB aggregation pipeline.

        Args:
            collection_name: Name of the collection to query
            pipeline: MongoDB aggregation pipeline

        Returns:
            List of processed Question objects
        """
        aggregation_results = await self.database_engine.run_aggregation(
            collection_name, self.database_name, pipeline
        )

        if not aggregation_results:
            return []

        flattened_questions = []
        for result in aggregation_results:
            for key, question_list in result.items():
                if isinstance(question_list, list):
                    flattened_questions.extend(question_list)
                else:
                    log.warning(
                        f"Unexpected data structure in aggregation result: {key}"
                    )

        return self._process_mongo_question_data(flattened_questions)

    async def get_question_by_custom_query(
        self, collection_name: str, query: dict[Any, Any]
    ) -> List[Question]:
        """
        Retrieve questions by a custom query.
        Args:
            collection_name: Name of the question collection/category
            query: Dictionary of question query parameters
        Returns:
            List of Question objects matching the provided identifiers

        """
        # TODO : add validators for empty query or collection name

        all_questions = []

        # consuming the generator content for now
        # since they're mostly a few question documents
        async for batch in await self.database_engine.fetch_from_db(
            collection_name, self.database_name, query
        ):
            all_questions.extend(batch)

        result = self._process_mongo_question_data(all_questions)
        log.info(
            "Retrieved %d questions out of %d requested IDs",
            len(result),
            len(all_questions),
        )

        return result

    @staticmethod
    def _validate_question_ids(question_ids: List[Dict[str, str]]) -> List[ObjectId]:
        """
        Validate and convert string IDs to MongoDB ObjectId instances.

        Args:
            question_ids: List of string IDs to validate and convert.

        Returns:
            List of valid MongoDB ObjectId instances.
        """
        log.debug("Validating %d question IDs", len(question_ids))
        object_ids = []
        invalid_count = 0

        for question_data in question_ids:
            try:
                if ObjectId.is_valid(question_data["id"]):
                    object_ids.append(ObjectId(question_data["id"]))
                else:
                    log.warning("Invalid ObjectId format: %s", question_data["id"])
                    invalid_count += 1
            except errors.InvalidId:
                log.warning("Failed to convert ID to ObjectId: %s", question_data["id"])
                invalid_count += 1

        if invalid_count > 0:
            log.warning(
                "Found %d invalid question IDs out of %d",
                invalid_count,
                len(question_ids),
            )

        if not object_ids:
            log.warning("No valid question IDs to query")
            return []

        log.debug("Successfully validated %d question IDs", len(object_ids))
        return object_ids

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
    def _process_mongo_question_data(
        questions: Iterable[Dict[str, Any]]
    ) -> List[Question]:
        """
        Process raw MongoDB documents into Question domain objects.

        Args:
            questions: Iterable of MongoDB document dictionaries.

        Returns:
            List of Question objects created from the MongoDB documents.
        """
        result: List[Question] = []
        error_count = 0

        for question in questions:
            try:
                question_id = str(question.get("_id", "unknown"))
                log.debug("Processing question data for ID: %s", question_id)

                question_with_string_id = {**question, "_id": question_id}
                question_obj = Question(**question_with_string_id)
                result.append(question_obj)

            except Exception as e:
                error_count += 1
                log.error(
                    "Error processing question data: %s. Error: %s",
                    question.get("_id", "unknown"),
                    str(e),
                    exc_info=e,
                )

        if error_count > 0:
            log.warning("Failed to process %d questions", error_count)

        log.debug("Successfully processed %d question objects", len(result))
        return result

    @classmethod
    def get_repo(cls):
        database_name = getattr(common, "NO_SQL_DATABASE_NAME", None)
        if database_name is None:
            log.error("NO_SQL_DATABASE_NAME not configured in settings")
            # TODO : raise custom error exception here for better details
            raise RuntimeError("NO_SQL_DATABASE_NAME not configured in settings")

        log.info("Creating MongoQuestionRepository instance")

        return MongoQuestionRepository(
            database_engine=mongo_database,
            database_name=database_name,
        )
