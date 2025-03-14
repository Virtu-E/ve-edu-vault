import logging
from collections import namedtuple
from typing import Set, List

from rest_framework.exceptions import ValidationError

from exceptions import ParsingError, QuestionNotFoundError
from repository.data_types import Question
from repository.question_respository import MongoQuestionRepository

from ..models import SubTopic, UserQuestionSet
from .mixins import RetrieveUserAndResourcesMixin

log = logging.getLogger(__name__)


Resources = namedtuple(
    "Resources", ("user", "sub_topic", "question_set_ids", "collection_name")
)


class QuestionService(RetrieveUserAndResourcesMixin):
    """
    Service class for handling question-related operations.

    This service provides functionality to validate questions, retrieve resources,
    and manage question collections based on user and topic context.

    Attributes:
        _serializer: The serializer containing validated data for the request.
    """

    def __init__(self, serializer) -> None:
        """
        Initialize the QuestionService with a serializer.

        Args:
            serializer: A serializer instance containing validated request data.
        """
        self._serializer = serializer
        self._user = self.get_user_from_validated_data(self._serializer)
        self._sub_topic = self.get_sub_topic_from_validated_data(self._serializer)
        self._collection_name = self._get_collection_name_from_topic(self._sub_topic)
        self._question_set_ids = None
        if not self._user or not self._sub_topic:
            # TODO : create a more meaningful error
            raise ValidationError("User and sub-topic must be provided.")
        self._question_set_ids = self.get_user_question_set(self._user, self._sub_topic)

    def validate_question_exists(self, question_id: str) -> bool:
        """
        Validate that a question ID exists in the given question set for a user.

        Args:
            question_id: The ID of the question to validate.

        Returns:
            True if the question exists in the set.

        Raises:
            QuestionNotFoundError: If the question ID is not found in the question set.
        """
        if question_id not in self._question_set_ids:
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

        The collection name is derived from the course key associated with the topic.

        Args:
            sub_topic: A SubTopic instance to extract the collection name from.

        Returns:
            The database collection name as a string.

        Raises:
            ValidationError: If the provided sub_topic is not a valid SubTopic instance.
            ParsingError: If the collection name cannot be determined from the sub_topic.
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

        Returns:
            A Resources namedtuple containing the user, sub_topic, question_set_ids,
            and collection_name.
        """

        return Resources(
            self._user, self._sub_topic, self._question_set_ids, self._collection_name
        )

    def get_questions_from_ids(self) -> List[Question]:
        """
        Retrieve Question objects based on the question IDs in the question set.

        This method uses the MongoQuestionRepository to fetch questions from the database
        using the collection name and question set IDs previously retrieved.

        Returns:
            List[Question]: A list of Question objects corresponding to the question IDs.
        """
        question_repo = MongoQuestionRepository.get_repo()
        questions = question_repo.get_questions_by_ids(
            collection_name=self._collection_name, question_ids=self._question_set_ids
        )
        return questions

    def is_grading_mode(self) -> bool:
        """
        Check if the user's question set is in grading mode.

        This method determines whether the UserQuestionSet for the current user and sub_topic
        has grading mode enabled.

        Returns:
            bool: True if grading mode is enabled, False otherwise.

        Note:
            If the UserQuestionSet does not exist, this method currently doesn't handle
            the error properly and returns None implicitly. This is marked with a TODO
            for future improvement.
        """
        try:
            return UserQuestionSet.objects.get(
                user_id=self._user, sub_topic=self._sub_topic
            ).grading_mode
        except UserQuestionSet.DoesNotExist:
            # TODO : process the error correctly here
            pass
