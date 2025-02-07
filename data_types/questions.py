from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic.v1 import validator


class Choice(BaseModel):
    text: str
    is_correct: bool = Field(
        exclude=True,
    )
    # TODO : introduce choice ID to allow randomization from the frontend
    # choice_id : int


class Solution(BaseModel):
    explanation: str
    steps: List[str]


class Metadata(BaseModel):
    created_by: str  # name of creator. If AI, specify the AI name
    created_at: datetime  # auto now add
    updated_at: datetime  # auto now add
    time_estimate: int  # minutes


class Question(BaseModel):
    id: str = Field(..., alias="_id")
    question_id: (
        str  # why am i including this here ? I feel like it will just create confusion
    )
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

    class Config:
        allow_population_by_field_name = True

    @validator("_id", pre=True, always=True)
    def ensure_string(cls, value):
        return str(value)


class QuestionAttemptData(BaseModel):
    is_correct: bool
    attempt_number: int
    difficulty: str
    topic: str
    question_id: str
    choice_id: Optional[int] = None
    total_correct_count: int
    total_incorrect_count: int
