from typing import Optional

from src.exceptions import VirtuEducateValidationError


class QuestionNotFoundError(VirtuEducateValidationError):
    """Raised when question is not found"""

    def __init__(
        self,
        question_id: str,
        user_id: Optional[str] = None,
        collection: Optional[str] = None,
        **kwargs,
    ):
        message = f"Question {question_id} not found"
        if user_id:
            message += f" for user {user_id}"
        if collection:
            message += f" in collection {collection}"

        super().__init__(message, **kwargs)

        self.question_id = question_id
        self.user_id = user_id
        self.collection = collection
        self.error_code = "QUESTION_NOT_FOUND"

        self.context = {
            "error_code": self.error_code,
            "question_id": question_id,
            "user_id": user_id,
            "collection": collection,
            "error_type": "not_found",
        }

        self.context = {k: v for k, v in self.context.items() if v is not None}
