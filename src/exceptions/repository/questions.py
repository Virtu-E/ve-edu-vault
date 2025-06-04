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

        self.error_code = "400"

        self.context = {
            k: v
            for k, v in {
                "question_id": question_id,
                "user_id": user_id,
                "collection": collection,
                "error_type": "QUESTION_NOT_FOUND",
            }.items()
            if v is not None
        }
