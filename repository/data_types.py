from datetime import datetime
from typing import List

from pydantic import BaseModel, Field
from pydantic.v1 import validator


class Choice(BaseModel):
    """
    Represents a single answer choice for a question.

    Attributes:
        text (str): The text content of the choice.
        is_correct (bool): Whether this choice is the correct answer. Hidden from API responses.
    """

    text: str
    is_correct: bool = Field(
        exclude=True,
    )
    # TODO : introduce choice ID to allow randomization from the frontend
    # choice_id : int


class Solution(BaseModel):
    """
    Contains the solution information for a question.

    Attributes:
        explanation (str): A detailed explanation of the solution.
        steps (List[str]): Step-by-step breakdown of how to solve the problem.
    """

    explanation: str
    steps: List[str]


class Metadata(BaseModel):
    """
    Stores metadata information about the question.

    Attributes:
        created_by (str): Name of the creator. If AI-generated, specifies the AI name.
        created_at (datetime): Timestamp when the question was created.
        updated_at (datetime): Timestamp when the question was last updated.
        time_estimate (int): Estimated time to solve the question in minutes.
    """

    created_by: str
    created_at: datetime
    updated_at: datetime
    time_estimate: int


class Question(BaseModel):
    """
    Represents a complete question with all its components.

    Attributes:
        id (str): Unique identifier for the question, aliased as "_id".
        text (str): The actual question text.
        topic (str): Main subject area the question belongs to.
        sub_topic (str): Specific sub-area within the main topic.
        academic_class (str): Academic class or grade level the question is intended for.
        examination_level (str): Level of examination (e.g., basic, intermediate, advanced).
        difficulty (str): Difficulty rating of the question.
        tags (list[str]): List of tags for categorization and searching.
        choices (list[Choice]): Available answer choices for the question.
        solution (Solution): Detailed solution information.
        hint (str): A hint to help answer the question.
        metadata (Metadata): Additional information about the question's creation and properties.
    """

    id: str = Field(..., alias="_id")
    text: str
    topic: str
    sub_topic: str
    academic_class: str
    examination_level: str
    difficulty: str
    tags: list[str]
    choices: list[Choice]
    solution: Solution
    hint: str
    metadata: Metadata

    class Config:
        """Configuration for the Question model."""

        allow_population_by_field_name = True

    @validator("_id", pre=True, always=True)
    def ensure_string(cls, value):
        """
        Ensures the ID is always stored as a string.

        Args:
            value: The ID value to validate.

        Returns:
            str: The ID converted to a string.
        """
        return str(value)
