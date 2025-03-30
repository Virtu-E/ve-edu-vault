from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


class QuestionMetadata(BaseModel):
    """
    Schema for a single question metadata entry in the UserQuestionAttempts django model.
    """

    question_id: str  # this is the mongo question ID
    attempt_number: int  # the maximum attempt number will be based on the users current learning mode : (Normal, reinforcement or recovery )
    is_correct: bool
    topic: str
    difficulty: Literal["easy", "medium", "hard"]
