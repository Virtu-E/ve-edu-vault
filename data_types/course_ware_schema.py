from typing import Any

from pydantic import BaseModel


class QuestionMetadata(BaseModel):
    """
    Schema for a single question metadata entry in the UserQuestionAttempts django model.
    """

    question_id: str
    attempt_number: int
    is_correct: bool
    topic: str
    difficulty: str


class UserQuestionAttemptsSchema(BaseModel):
    """
    Pydantic model for user question attempts ( UserQuestionAttempts ) django model.
    """

    user_id: int
    topic_id: int
    question_metadata: dict[str, dict[str, QuestionMetadata | Any]]
    # Top-level key: Version (e.g., "v1.0.0")
    # Second-level key: Question ID (e.g., "q123")

    model_config = {"from_attributes": True}
