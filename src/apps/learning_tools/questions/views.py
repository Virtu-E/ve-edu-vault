class GetQuestionsView(QuestionServiceMixin, CustomRetrieveAPIView):
    """
    API view to retrieve questions for a specific user and learning_objective.

    This view fetches questions based on the provided username and block_id,
    with optional filtering by grading mode.
    """

    serializer_class = QueryParamsSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Override the retrieve method to implement our custom logic.
        """
        serializer = self.get_serializer(data=kwargs)
        question_service_bundle = self.get_validated_service_resources(
            kwargs, serializer
        )
        question_data = []

        if not question_service_bundle.resources.question_set_ids:
            log.info(
                "No valid question IDs found for user %s",
                question_service_bundle.validated_data["username"],
            )
            return Response(
                {
                    "message": f"No valid question IDs found for user {question_service_bundle.validated_data['username']}",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        grading_mode = question_service_bundle.service.is_grading_mode()

        # Only fetch questions if not in grading mode
        if not grading_mode:
            question_data = async_to_sync(
                question_service_bundle.service.get_questions_from_ids
            )()

        return Response(
            {
                "username": question_service_bundle.validated_data["username"],
                "block_id": question_service_bundle.validated_data["block_id"],
                "questions": question_data,
                "grading_mode": grading_mode,
            },
            status=status.HTTP_200_OK,
        )


class GetQuestionAttemptView(QuestionServiceMixin, CustomRetrieveAPIView):
    """
    API view to retrieve all question attempts for a user and learning_objective.

    This view returns a summary of all attempts made by a user for questions
    in a specific learning objective.
    """

    serializer_class = UserQuestionAttemptSerializer

    def retrieve(self, request, *args, **kwargs):
        return async_to_sync(self._async_retrieve)(request, *args, **kwargs)

    async def _async_retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=kwargs)
        question_service_bundle = await self.get_validated_service_resources_async(
            kwargs, serializer
        )

        grading_response_service = GradingResponseService.get_service(
            collection_name=question_service_bundle.resources.collection_name
        )

        assessment_id = await get_assessment_id(
            user=question_service_bundle.resources.user,
            learning_objective=question_service_bundle.resources.learning_objective,
        )
        question_attempts = await grading_response_service.get_grading_responses(
            user_id=question_service_bundle.resources.user.id,
            collection_name=question_service_bundle.resources.collection_name,
            assessment_id=assessment_id,
        )

        return Response(
            data={model.question_id: model.model_dump() for model in question_attempts},
            status=status.HTTP_200_OK,
        )


# TODO : catch and handle this error : QuestionNotFoundError
class PostQuestionAttemptView(QuestionServiceMixin, CustomUpdateAPIView):
    """
    View that handles a question attempt submission.

    This view processes student answers to questions, grades them using the appropriate grader,
    saves the attempt results, and returns the grading response.
    """

    serializer_class = PostQuestionAttemptSerializer

    def post(self, request, **kwargs):
        """
        Handle POST requests by delegating to the async implementation.

        Args:
            request: The HTTP request object
            **kwargs: Additional keyword arguments passed to the view

        Returns:
            Response: The HTTP response containing grading results
        """
        return async_to_sync(self._async_post)(request, **kwargs)

    async def _async_post(self, request, **kwargs):
        """
        Asynchronous implementation of the POST request handler.

        This method:
        1. Validates the request data
        2. Retrieves necessary resources
        3. Gets the appropriate grader
        4. Fetches the question and any existing attempt concurrently
        5. Grades the attempted answer
        6. Saves the attempt and grading response concurrently
        7. Returns the grading result

        Args:
            request: The HTTP request object
            **kwargs: Additional keyword arguments containing request data

        Returns:
            Response: HTTP response with grading results and 201 Created status
        """
        serializer = self.get_serializer(data=request.data)
        question_service_bundle = await self.get_validated_service_resources_async(
            request.data, serializer
        )

        question_id = question_service_bundle.validated_data["question_id"]

        grader = SingleQuestionGrader.get_grader(
            question_service_bundle.resources.collection_name
        )
        assessment_id = await get_assessment_id(
            user=question_service_bundle.resources.user,
            learning_objective=question_service_bundle.resources.learning_objective,
        )

        question, question_attempt = await asyncio.gather(
            question_service_bundle.service.get_question_by_id(question_id),
            grader.get_question_attempt(
                user_id=question_service_bundle.resources.user.id,
                question_id=question_id,
                assessment_id=assessment_id,
            ),
        )

        attempted_answer = AttemptedAnswer(
            question_type=question_service_bundle.validated_data["question_type"],
            question_metadata=question_service_bundle.validated_data[
                "question_metadata"
            ],
        )

        grading_result = grader.grade(
            user_id=question_service_bundle.resources.user.id,
            attempted_answer=attempted_answer,
            question=question,
            question_attempt=question_attempt,
        )

        grading_response_service = GradingResponseService.get_service(
            collection_name=question_service_bundle.resources.collection_name
        )
        if grading_result.success:
            await asyncio.gather(
                grader.save_attempt(
                    user_id=question_service_bundle.resources.user.id,
                    question=question,
                    is_correct=grading_result.is_correct,
                    score=grading_result.score,
                    assessment_id=assessment_id,
                    question_attempt=question_attempt,
                ),
                grading_response_service.save_grading_response(
                    user_id=question_service_bundle.resources.user.id,
                    question_id=question_id,
                    assessment_id=assessment_id,
                    grading_response=grading_result,
                    question_type=question.question_type,
                ),
            )

        return Response(
            {question.id: grading_result.to_dict()},
            status=status.HTTP_201_CREATED,
        )
