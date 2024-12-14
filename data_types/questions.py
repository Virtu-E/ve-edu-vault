from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List


@dataclass
class Choice:
    text: str
    is_correct: bool


@dataclass
class Solution:
    explanation: str


@dataclass
class Metadata:
    created_by: str
    created_at: datetime
    updated_at: datetime


@dataclass
class Question:
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
