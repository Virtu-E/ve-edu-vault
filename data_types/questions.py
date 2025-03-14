from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic.v1 import validator


class QuestionAttemptData(BaseModel):
    is_correct: bool
    attempt_number: int
    difficulty: str
    topic: str
    question_id: str
    choice_id: Optional[int] = None
    total_correct_count: int
    total_incorrect_count: int
