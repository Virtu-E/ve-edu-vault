from datetime import datetime
from typing import List

from pydantic import BaseModel
from pydantic.v1 import validator


class Choice(BaseModel):
    text: str
    is_correct: bool


class Solution(BaseModel):
    explanation: str
    steps: List[str]


class Metadata(BaseModel):
    created_by: str  # name of creator. If AI, specify the AI name
    created_at: datetime  # auto now add
    updated_at: datetime  # auto now add
    time_estimate: int  # minutes


class Question(BaseModel):
    _id: str  # skip this, will be auto generated when we insert questions to mongo
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

    @validator("_id", pre=True, always=True)
    def ensure_string(cls, value):
        return str(value)


class QuestionAttemptData(BaseModel):
    is_correct: bool
    in_correct_count: int = 0
    question_id: str
    category_id: str
    topic_id: str
