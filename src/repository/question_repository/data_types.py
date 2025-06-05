from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


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


class Blank(BaseModel):
    """
    Represents a single blank in a fill-in-the-blank question.

    Attributes:
        id (int): The identifier for the blank (e.g., 1, 2, 3).
        position (int): The position of the blank in the question text.
        accepted_answers (List[str]): List of acceptable answers for this blank.
        case_sensitive (bool): Whether the answer matching should be case sensitive.
        exact_match (bool): Whether the answer must match exactly or allow partial matching.
    """

    id: int
    position: int
    accepted_answers: List[str] = Field(exclude=True)
    case_sensitive: bool = Field(default=False, exclude=True)
    exact_match: bool = Field(default=True, exclude=True)


class Content(BaseModel):
    """
    Contains the content for different question types.

    Attributes:
        options (Optional[List[Option]]): Available answer options for multiple-choice questions.
        blanks (Optional[List[Blank]]): Blank configurations for fill-in-the-blank questions.
    """

    options: Optional[List[Option]] = None
    blanks: Optional[List[Blank]] = None


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
        question_type (str): Type of question (e.g., "multiple-choice", "fill-in-the-blank").
        content (Content): The content of the question including options or blanks.
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

    @field_serializer("created_at", "updated_at")
    def serialize_datetimes(self, dt: datetime, _info):
        return dt.isoformat()

    model_config = ConfigDict(populate_by_name=True)
