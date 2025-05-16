from collections import namedtuple

from asgiref.sync import sync_to_async

from src.lib.education_service import EducationalContextService

ServiceResources = namedtuple(
    "ServiceResources",
    [
        "validated_data",
        "service",
        "resources",
    ],
)


class EducationContextMixin:
    """
    Mixin that provides common functionality for views that need to:
    1. Validate serializer data
    2. Create a QuestionService
    3. Get resources from the service

    Returns a namedtuple with dot notation access to all components.
    """

    @staticmethod
    def get_validated_service_resources(data_dict, serializer):
        """
        Synchronous method to validate data and get QuestionService resources.

        Args:
            data_dict: Dictionary containing data to validate (typically request.data or kwargs)

        Returns:
            ServiceResources: A namedtuple with validated_data, service, and resources
        """
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        service = EducationalContextService(data=validated_data)
        resources = service.get_resources()

        return ServiceResources(
            validated_data=validated_data, service=service, resources=resources
        )

    @staticmethod
    async def get_validated_service_resources_async(data_dict, serializer):
        """
        Asynchronous method to validate data and get QuestionService resources.

        Args:
            data_dict: Dictionary containing data to validate (typically request.data or kwargs)

        Returns:
            ServiceResources: A namedtuple with validated_data, service, and resources
        """
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        service = await sync_to_async(EducationalContextService)(data=validated_data)
        resources = service.get_resources()

        return ServiceResources(
            validated_data=validated_data, service=service, resources=resources
        )
