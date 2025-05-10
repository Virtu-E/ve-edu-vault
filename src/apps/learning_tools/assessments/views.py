from asgiref.sync import async_to_sync, sync_to_async
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView


# Create your views here.
class AssessmentCompletionView(CustomUpdateAPIView):
    # TODO : one thing we need to implement is Authorization, Authentication and Auditing for the API endpoints
    """
    View to handle the completion of a quiz/challenge.
    """

    serializer_class = QueryParamsSerializer


class AssessmentStartView(QuestionServiceMixin, CustomRetrieveAPIView):
    """
    View to handle the start of an assessment.
    """

    serializer_class = QueryParamsSerializer

    def retrieve(self, request, *args, **kwargs):
        return async_to_sync(self._async_retrieve)(request, *args, **kwargs)

    async def _async_retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=kwargs)
        question_service_bundle = await self.get_validated_service_resources_async(
            request.data, serializer
        )
        user = question_service_bundle.resources.user
        learning_objective = question_service_bundle.resources.learning_objective

        if assessment := await sync_to_async(UserAssessmentAttempt.get_active_attempt)(
            user=user, learning_objective=learning_objective
        ):
            return Response(
                data={"assessment_id": assessment.assessment_id},
                status=status.HTTP_200_OK,
            )

        assessment, _ = await sync_to_async(
            UserAssessmentAttempt.get_or_create_attempt
        )(user=user, learning_objective=learning_objective)

        return Response(
            data={"assessment_id": assessment.assessment_id},
            status=status.HTTP_200_OK,
        )


class HasActiveAssessmentView(QuestionServiceMixin, CustomRetrieveAPIView):
    """View that checks if the user has an active assessment."""

    serializer_class = QueryParamsSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Synchronous entry point that delegates to the async implementation.
        """
        return async_to_sync(self._async_retrieve)(request, *args, **kwargs)

    async def _async_retrieve(self, request, *args, **kwargs):
        """
        Asynchronous implementation that fetches assessment data concurrently.
        """
        serializer = self.get_serializer(data=kwargs)
        question_service_bundle = await self.get_validated_service_resources_async(
            kwargs, serializer
        )

        user = question_service_bundle.resources.user
        learning_objective = question_service_bundle.resources.learning_objective

        try:
            assessment, assessment_questions = await asyncio.gather(
                sync_to_async(UserAssessmentAttempt.get_active_attempt)(
                    user=user, learning_objective=learning_objective
                ),
                sync_to_async(UserQuestionSet.objects.get)(
                    user=user, learning_objective=learning_objective
                ),
            )
        except UserQuestionSet.DoesNotExist:
            return Response(
                {
                    "error": "No question set found for this user and learning objective."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        num_questions = len(list(assessment_questions.question_list_ids))

        if assessment:
            return Response(
                data={
                    "assessment_id": assessment.assessment_id,
                    "has_active": True,
                    "num_questions": num_questions,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            data={
                "assessment_id": None,
                "has_active": False,
                "num_questions": num_questions,
            },
            status=status.HTTP_200_OK,
        )
