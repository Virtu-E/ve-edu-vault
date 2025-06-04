import logging
from typing import Dict, List

from django.shortcuts import get_object_or_404

from src.apps.core.content.models import LearningObjective, SubTopic
from src.apps.core.users.models import EdxUser
from src.apps.learning_tools.questions.models import DefaultQuestionSet, UserQuestionSet
from src.exceptions import VirtuEducateValidationError

log = logging.getLogger(__name__)


class UserResourceContextMixin:
    """
    Mixin to retrieve User, LearningObjective, UserQuestionSet, and related
    resources based on validated serializer data.
    """

    @staticmethod
    def get_edx_user_from_username(username) -> EdxUser:
        """
        Retrieve a User object based on 'username'.

        Args:
            username: The username of the user.

        Returns:
            EdxUser: The retrieved User object.
        """
        return get_object_or_404(EdxUser, username=username)

    @staticmethod
    def get_learning_objective_from_block_id(block_id) -> LearningObjective:
        """
        Retrieve a LearningObjective object based on 'block_id'.

        Args:
            block_id: The block ID of the learning objective.

        Returns:
            LearningObjective: The retrieved LearningObjective object.
        """
        return get_object_or_404(LearningObjective, block_id=block_id)

    @staticmethod
    def get_user_question_set(
        user: EdxUser, objective: LearningObjective
    ) -> List[Dict[str, str]]:
        """
        Retrieve the UserQuestionSet object for the given user and learning objective.

        Args:
            user: The User object.
            objective: The LearningObjective object.

        Returns:
            List[Dict[str, str]]: The question list IDs from the UserQuestionSet.
        """
        # The first requirement is for the default question set to exist
        default_question_set = get_object_or_404(
            DefaultQuestionSet, learning_objective=objective
        )
        user_question_set, created = UserQuestionSet.objects.get_or_create(
            user=user,
            learning_objective=objective,
            defaults={"question_list_ids": default_question_set.questions},
        )
        return user_question_set.question_list_ids

    @staticmethod
    def get_collection_name_from_subtopic(sub_topic: SubTopic) -> str:
        """
        Extract the database collection name from a SubTopic instance.

        Args:
            sub_topic: A SubTopic instance containing the course information.

        Returns:
            str: The database collection name derived from the course key.

        Raises:
            ValidationError: If the provided sub_topic is not a valid SubTopic instance.
            ParsingError: If the course key cannot be determined from the sub_topic.
        """
        if not isinstance(sub_topic, SubTopic):
            log.error("Invalid topic instance: not a SubTopic object")
            raise VirtuEducateValidationError("Invalid topic instance: expected SubTopic object")

        course_id = sub_topic.topic.course.course_key
        if not course_id:
            log.error(
                "Could not find database collection associated with the course ID: %s",
                course_id,
            )
            raise VirtuEducateValidationError(f"Could not find database collection associated with the course ID: {course_id}")


        return course_id
