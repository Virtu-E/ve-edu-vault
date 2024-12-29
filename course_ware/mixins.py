from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from course_ware.models import Topic, User, UserQuestionSet


class RetrieveUserAndResourcesMixin:
    """
    Mixin to retrieve a User, Topic, and UserQuestionSet object based on
    validated serializer data.
    """

    @staticmethod
    def get_user_from_validated_data(serializer) -> User:
        """
        Retrieve a User object based on 'username' from validated serializer data.

        Args:
            serializer: The serializer containing validated data.

        Returns:
            User: The retrieved User object.

        Raises:
            ValidationError: If 'username' is not in the validated data.
        """
        if "username" not in serializer.validated_data:
            raise ValidationError({"username": "Username is required."})
        return get_object_or_404(User, username=serializer.validated_data["username"])

    # TODO : i have to provide more data like category, course etc
    @staticmethod
    def get_topic_from_validated_data(serializer) -> Topic:
        """
        Retrieve a Topic object based on 'topic_id' from validated serializer data.

        Args:
            serializer: The serializer containing validated data.

        Returns:
            Topic: The retrieved Topic object.

        Raises:
            ValidationError: If 'topic_id' is not in the validated data.
        """
        if "topic_id" not in serializer.validated_data:
            raise ValidationError({"topic_id": "Topic ID is required."})
        return get_object_or_404(Topic, block_id=serializer.validated_data["topic_id"])

    @staticmethod
    def get_user_question_set(user, topic):
        """
        Retrieve the UserQuestionSet object for the given user and topic.

        Args:
            user (User): The User object.
            topic (Topic): The Topic object.

        Returns:
            UserQuestionSet: The retrieved UserQuestionSet object.
        """
        return get_object_or_404(UserQuestionSet, user=user, topic=topic)
