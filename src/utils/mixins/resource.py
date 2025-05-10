from typing import Dict, List

from django.shortcuts import get_object_or_404

from course_ware.models import (
    DefaultQuestionSet,
    EdxUser,
    LearningObjective,
    UserQuestionSet,
)


class UserResourceContextMixin:
    """
    Mixin to retrieve a User, Topic, and UserQuestionSet object based on
    validated serializer data.
    """

    @staticmethod
    def get_edx_user_from_username(username) -> EdxUser:
        """
        Retrieve a User object based on 'username'.

        Args:
            username: The username of the user.

        Returns:
            User: The retrieved User object.

        """

        return get_object_or_404(EdxUser, username=username)

    # TODO : i have to provide more data like category, course etc
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
            user (EdxUser): The User object.
            objective (LearningObjective): The LearningObjective object.

        Returns:
            UserQuestionSet: The retrieved UserQuestionSet object.
        """
        # the first requirement is for the default question set to exist
        default_question_set = get_object_or_404(
            DefaultQuestionSet, learning_objective=objective
        )
        user_question_set, created = UserQuestionSet.objects.get_or_create(
            user=user,
            learning_objective=objective,
            defaults={"question_list_ids": default_question_set.question_list_ids},
        )
        return user_question_set.question_list_ids
