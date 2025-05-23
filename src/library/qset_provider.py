import logging
from collections import namedtuple
from typing import Dict

from src.exceptions import QuestionNotFoundError
from src.repository.question_repository.mongo_qn_repository import (
    MongoQuestionRepository,
)
from src.utils.mixins.resource import UserResourceContextMixin

log = logging.getLogger(__name__)


Resources = namedtuple(
    "Resources", ("user", "learning_objective", "question_set_ids", "collection_name")
)


class QuestionSetResourceProvider(UserResourceContextMixin):
    """
    Service class for providing question set resources and context.

    This service manages the retrieval and validation of resources required for
    question set operations, including users, learning objectives, and question sets.
    """

    def __init__(self, data: Dict[str, str]) -> None:
        """
        Initialize the provider with validated request data.

        Args:
            data: Validated data dictionary containing 'username' and 'block_id' keys.

        Raises:
            ValidationError: If the user or learning objective cannot be retrieved.
        """
        self._data = data
        self._initialize_resources()

    def _initialize_resources(self) -> None:
        """Initialize all required resources and validate their existence."""
        self._user = self.get_edx_user_from_username(self._data["username"])
        self._learning_objective = self.get_learning_objective_from_block_id(
            self._data["block_id"]
        )

        self._collection_name = self.get_collection_name_from_subtopic(
            self._learning_objective.sub_topic
        )
        self._question_set_ids = self.get_user_question_set(
            self._user, self._learning_objective
        )
        self._question_repo = MongoQuestionRepository.get_repo()

    def _validate_question_exists(self, question_id: str) -> bool:
        """
        Validate that a question ID exists in the question set for the current user.

        Args:
            question_id: The ID of the question to validate.

        Returns:
            bool: True if the question exists in the user's question set.

        Raises:
            QuestionNotFoundError: If the question ID is not found.
        """
        question_ids = {question["id"] for question in self._question_set_ids}
        if question_id not in question_ids:
            log.error(
                "Question ID '%s' not found in question set for user '%s'",
                question_id,
                self._user,
            )
            raise QuestionNotFoundError(question_id, self._user)
        return True

    def get_resources(self) -> Resources:
        """
        Retrieve all resources needed for question set operations.

        Returns:
            Resources: A namedtuple containing all necessary question set resources.

        Raises:
            QuestionNotFoundError: If a question_id is provided but not found.
        """
        if question_id := self._data.get("question_id"):
            self._validate_question_exists(question_id)

        return Resources(
            self._user,
            self._learning_objective,
            self._question_set_ids,
            self._collection_name,
        )
