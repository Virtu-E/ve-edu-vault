from typing import Dict, Any, Optional

from decouple import config
from rest_framework import status
from rest_framework.response import Response

from course_ware.models import UserQuestionAttempts
from data_types.questions import QuestionAttemptData
from repository.data_types import Question
from repository.question_respository import MongoQuestionRepository

MAX_ATTEMPTS = config("MAX_QUESTION_ATTEMPTS", default=3, cast=int)


class QuestionAttemptService:
    def __init__(
        self,
        collection_name: str,
        metadata: Dict[str, Any],
        question_id: str,
        choice_id: int,
        sub_topic_name: str,
        difficulty: str,
    ):
        self._collection_name = collection_name
        self._metadata = metadata
        self._question_id = question_id
        self._choice_id = choice_id
        self._sub_topic_name = sub_topic_name
        self._difficulty = difficulty
        self._question_repo = MongoQuestionRepository.get_repo()

    def process_question(self, user_question_attempt: UserQuestionAttempts) -> Response:
        """
        Process a question attempt and return the appropriate response.

        Args:
            user_question_attempt: The user's question attempt object

        Returns:
            Response: REST framework response with appropriate status code
        """
        if self._question_id not in self._metadata:
            self._metadata[self._question_id] = self._create_question_metadata()
        else:
            response = self._handle_existing_attempt()
            if response:
                return response

            # Update metadata with new attempt info
            self._metadata[self._question_id] = self._update_question_metadata()
            self._metadata[self._question_id]["choice_id"] = self._choice_id

        # Save the attempt
        user_question_attempt.save()

        # Return success response with attempt data
        return Response(
            QuestionAttemptData(
                **self._metadata[self._question_id],
                total_incorrect_count=user_question_attempt.get_incorrect_questions_count,
                total_correct_count=user_question_attempt.get_correct_questions_count,
            ).model_dump(),
            status=status.HTTP_201_CREATED,
        )

    def _handle_existing_attempt(self) -> Optional[Response]:
        """
        Handle logic for an existing question attempt.

        Returns:
            Optional[Response]: Response if attempt should be blocked, None if attempt can proceed
        """
        question_metadata = self._metadata.get(self._question_id)

        if question_metadata["is_correct"]:
            return Response(
                {"message": "Question already correctly answered"},
                status=status.HTTP_409_CONFLICT,
            )

        if question_metadata["attempt_number"] >= MAX_ATTEMPTS:
            return Response(
                {"message": f"Maximum attempts ({MAX_ATTEMPTS}) reached"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        return None

    def _is_choice_correct(self, question_instance: Question, choice_id: int) -> bool:
        """
        Check if the selected choice is correct.

        Args:
            question_instance: The question object
            choice_id: The ID of the selected choice

        Returns:
            bool: True if the choice is correct, False otherwise
        """
        try:
            return question_instance.choices[choice_id].is_correct
        except (IndexError, AttributeError):
            # TODO : add better error warning
            raise Exception("Invalid choice id")

    def _is_choice_answer_correct(self) -> bool:
        """
        Check if the user's selected choice is correct for the current question.

        Returns:
            bool: True if the choice is correct, False otherwise
        """
        question = self._question_repo.get_question_by_single_id(
            collection_name=self._collection_name, question_id=self._question_id
        )
        if not question:
            return False

        return self._is_choice_correct(question, self._choice_id)

    def _update_question_metadata(self) -> Dict[str, Any]:
        """
        Update the metadata for a question attempt.

        Returns:
            Dict[str, Any]: Updated question metadata
        """
        question_metadata = self._metadata.get(self._question_id, {})
        is_correct = self._is_choice_answer_correct()

        return {
            **question_metadata,
            "is_correct": is_correct,
            "attempt_number": question_metadata.get("attempt_number", 0) + 1,
        }

    def _create_question_metadata(self) -> Dict[str, Any]:
        """
        Create new metadata for a first question attempt.

        Returns:
            Dict[str, Any]: New question metadata
        """
        return {
            "is_correct": self._is_choice_answer_correct(),
            "attempt_number": 1,
            "difficulty": self._difficulty,
            "topic": self._sub_topic_name,
            "question_id": self._question_id,
        }
