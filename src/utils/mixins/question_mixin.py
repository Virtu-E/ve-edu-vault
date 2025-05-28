from collections import namedtuple

from asgiref.sync import sync_to_async

from src.library.qset_provider import QuestionSetResourceProvider

QuestionSetResources = namedtuple(
    "QuestionSetResources",
    [
        "validated_data",
        "resources",
    ],
)


class QuestionSetMixin:
    """
    Mixin that provides common functionality for views that need to:
    1. Validate serializer data
    2. Create a QuestionSetResourceProvider
    3. Get resources from the provider

    Returns a namedtuple with dot notation access to all components.
    """

    @staticmethod
    def get_validated_question_set_resources(serializer) -> QuestionSetResources:
        """
        Synchronous method to validate data and get question set resources.

        Returns:
            QuestionSetResources: A namedtuple with validated_data and resources
        """
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        provider = QuestionSetResourceProvider(data=validated_data)
        resources = provider.get_resources()

        return QuestionSetResources(validated_data=validated_data, resources=resources)

    @staticmethod
    async def get_validated_question_set_resources_async(
        serializer,
    ) -> QuestionSetResources:
        """
        Asynchronous method to validate data and get question set resources.

        Returns:
            QuestionSetResources: A namedtuple with validated_data and resources
        """
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        provider = await sync_to_async(QuestionSetResourceProvider)(data=validated_data)
        resources = provider.get_resources()

        return QuestionSetResources(validated_data=validated_data, resources=resources)
