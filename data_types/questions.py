from datetime import datetime
from typing import List

from pydantic import BaseModel


class Choice(BaseModel):
    text: str
    is_correct: bool


class Solution(BaseModel):
    explanation: str


class Metadata(BaseModel):
    created_by: str
    created_at: datetime
    updated_at: datetime


class Question(BaseModel):
    _id: str
    question_id: str
    text: str
    topic: str
    category: str
    academic_class: str
    examination_level: str
    difficulty: str
    tags: list[str]
    choices: list[Choice]
    solution: Solution
    hint: str
    metadata: Metadata


class QuestionAttemptData(BaseModel):
    is_correct: bool
    in_correct_count: int = 0
    question_id: str
    category_id: str
    topic_id: str
