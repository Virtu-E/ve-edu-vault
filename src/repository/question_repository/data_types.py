from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class Option(BaseModel):
    """
    Represents a single answer option for a question.

    Attributes:
        id (str): The identifier for the option (e.g., "A", "B", "C").
        text (str): The text content of the option.
        is_correct (bool): Whether this option is the correct answer. Hidden from API responses.
    """

    id: str
    text: str
    is_correct: bool = Field(exclude=True)


class Content(BaseModel):
    """
    Contains the options for a multiple-choice question.

    Attributes:
        options (List[Option]): Available answer options for the question.
    """

    options: List[Option]


class Solution(BaseModel):
    """
    Contains the solution information for a question.

    Attributes:
        explanation (str): A detailed explanation of the solution.
        steps (List[str]): Step-by-step breakdown of how to solve the problem.
    """

    explanation: str
    steps: List[str]


class Question(BaseModel):
    """
    Represents a complete question with all its components.

    Attributes:
        id (str): Unique identifier for the question, aliased as "_id".
        category_id (str): Identifier for categorizing the question.
        text (str): The actual question text.
        topic (str): Main subject area the question belongs to.
        sub_topic (str): Specific sub-area within the main topic.
        learning_objective (str): The learning objective addressed by the question.
        academic_class (str): Academic class or grade level the question is intended for.
        examination_level (str): Level of examination (e.g., JCE).
        difficulty (str): Difficulty rating of the question.
        tags (List[str]): List of tags for categorization and searching.
        question_type (str): Type of question (e.g., "multiple-choice").
        content (Content): The content of the question including options.
        solution (Solution): Detailed solution information.
        hint (str): A hint to help answer the question.
        possible_misconception (str): Common misconceptions related to the question.
        created_at (datetime): Timestamp when the question was created.
        updated_at (datetime): Timestamp when the question was last updated.
    """

    id: str = Field(alias="_id")
    category_id: str
    text: str
    topic: str
    sub_topic: str
    learning_objective: str
    academic_class: str
    examination_level: str
    difficulty: str
    tags: List[str]
    question_type: str
    content: Content
    solution: Solution = Field(exclude=True)
    hint: str = Field(exclude=True)
    possible_misconception: str = Field(exclude=True)
    created_at: datetime
    updated_at: datetime

    class Config:
        """Configuration for the Question model."""

        populate_by_name = (
            True  # Replaces allow_population_by_field_name in newer versions
        )
        json_encoders = {datetime: lambda v: v.strftime("%Y-%m-%dT%H:%M:%SZ")}
