import logging
from collections import namedtuple
from typing import Dict, List

from rest_framework.exceptions import ValidationError

from exceptions import ParsingError, QuestionNotFoundError
from repository.question_repository.mongo_qn_repository import MongoQuestionRepository
from repository.question_repository.qn_repository_data_types import Question

from ..models import SubTopic
from .mixins import RetrieveUserAndResourcesMixin

log = logging.getLogger(__name__)


Resources = namedtuple(
    "Resources", ("user", "learning_objective", "question_set_ids", "collection_name")
)


class QuestionService(RetrieveUserAndResourcesMixin):
    """
    Service class for handling question-related operations.

    This service provides functionality to validate questions, retrieve resources,
    and manage question collections based on user and learning objective context.
    It serves as an intermediary between the API endpoints and the data repositories,
    ensuring proper validation and error handling.

    Attributes:
        _data (Dict[str, str]): The validated data dictionary for the request.
        _user (EdxUser): The user associated with the request.
        _learning_objective (LearningObjective): The learning objective associated with the request.
        _collection_name (str): The database collection name derived from the course key.
        _question_set_ids (List[str]): List of question IDs associated with the user and learning objective.
    """

    def __init__(self, data: Dict[str, str]) -> None:
        """
        Initialize the QuestionService with validated request data.

        Retrieves and initializes all necessary resources including the user,
        learning objective, collection name, and question set IDs required for
        subsequent operations.

        Args:
            data (Dict[str, str]): Validated data dictionary containing at minimum
                                  'username' and 'block_id' keys.

        Raises:
            ValidationError: If the user or learning objective cannot be retrieved
                            from the provided data.
        """
        self._data = data
        self._user = self.get_edx_user_from_username(data["username"])
        self._learning_objective = self.get_learning_objective_from_block_id(
            data["block_id"]
        )
        self._collection_name = self._get_collection_name_from_topic(
            self._learning_objective.sub_topic
        )
        if not self._user or not self._learning_objective:
            # TODO : create a more meaningful error
            raise ValidationError("User and learning objective must be provided.")
        self._question_set_ids = self.get_user_question_set(
            self._user, self._learning_objective
        )
        self._question_repo = MongoQuestionRepository.get_repo()

    def _validate_question_exists(self, question_id: str) -> bool:
        """
        Validate that a question ID exists in the question set for the current user.

        Checks if the provided question ID is present in the user's question set
        associated with the current learning objective.

        Args:
            question_id (str): The ID of the question to validate.

        Returns:
            bool: True if the question exists in the user's question set.

        Raises:
            QuestionNotFoundError: If the question ID is not found in the user's question set.
                                  Includes details about the missing question ID and user.
        """
        if question_id not in {question["id"] for question in self._question_set_ids}:
            log.error(
                "Question ID '%s' not found in question set for user '%s'",
                question_id,
                self._user,
            )
            raise QuestionNotFoundError(question_id, self._user)
        return True

    @staticmethod
    def _get_collection_name_from_topic(sub_topic: SubTopic) -> str:
        """
        Extract the database collection name from a SubTopic instance.

        Determines the appropriate database collection name based on the course key
        associated with the provided sub_topic. This collection name is used for
        subsequent database operations.

        Args:
            sub_topic (SubTopic): A SubTopic instance containing the course information.

        Returns:
            str: The database collection name derived from the course key.

        Raises:
            ValidationError: If the provided sub_topic is not a valid SubTopic instance.
            ParsingError: If the course key cannot be determined from the sub_topic or
                         if no collection is associated with the course key.
        """
        if not isinstance(sub_topic, SubTopic):
            log.error("Invalid topic instance: not a SubTopic object")
            raise ValidationError("Invalid topic instance: expected SubTopic object")

        course_id = sub_topic.topic.course.course_key
        if not course_id:
            log.error(
                "Could not find database collection associated with the course ID: %s",
                course_id,
            )
            raise ParsingError(
                f"Could not find database collection associated with the course ID: {course_id}"
            )
        return course_id

    def get_resources(self) -> Resources:
        """
        Retrieve all resources needed for question operations.

        Gathers and returns the essential resources needed for question-related operations,
        including user information, learning objective details, question set IDs, and
        database collection name. Validates any question ID provided in the request data.

        Returns:
            Resources: A namedtuple containing:
                - user: The EdxUser instance
                - learning_objective: The LearningObjective instance
                - question_set_ids: List of question IDs associated with the user and learning objective
                - collection_name: The database collection name for question retrieval

        Raises:
            QuestionNotFoundError: If a question_id is provided in the data but not found
                                  in the user's question set.
        """
        if value := self._data.get("question_id"):
            self._validate_question_exists(value)

        return Resources(
            self._user,
            self._learning_objective,
            self._question_set_ids,
            self._collection_name,
        )

    async def get_questions_from_ids(self) -> List[Dict]:
        """
        Retrieve Question objects based on the question IDs in the user's question set
        and convert them to dictionaries for serialization.

        Fetches the complete Question objects from the database using the collection name
        and question set IDs, then converts them to dictionaries that can be easily
        serialized to JSON or other formats.

        Returns:
            List[Dict]: A list of serialized Question objects corresponding to the
                       question IDs in the user's question set.
        """

        questions = await self._question_repo.get_questions_by_ids(
            collection_name=self._collection_name, question_ids=self._question_set_ids
        )

        # Convert Pydantic models to dictionaries
        dumped_questions = [question.model_dump() for question in questions]
        return dumped_questions

    async def get_question_by_id(self, question_id: str) -> Question:
        """
        Retrieve a Question object based on the question ID from mongo db
        """

        question = await self._question_repo.get_question_by_single_id(
            collection_name=self._collection_name, question_id=question_id
        )
        return question

    def is_grading_mode(self) -> bool:
        """
        Check if the user's question set is in grading mode.

        Determines whether the current question set for the user and learning objective
        has grading mode enabled. Grading mode affects how question responses are
        evaluated and scored.

        Returns:
            bool: True if grading mode is enabled, False otherwise.

        Note:
            This method is currently a placeholder that always returns False.
            The commented code shows the intended implementation for future completion.
        """
        # TODO: to be implemented
        return False
        # try:
        #     return UserQuestionSet.objects.get(
        #         user_id=self._user, sub_topic=self._sub_topic
        #     ).grading_mode
        # except UserQuestionSet.DoesNotExist:
        #     # TODO : process the error correctly here
        #     pass
