from typing import Literal

from pydantic import BaseModel, Field, constr


class PerformanceStats(BaseModel):
    """
    Stores comprehensive performance statistics.

    Attributes:
        ranked_difficulties: List of question difficulty rankings ordered by average question attempts per difficulty
        difficulty_status: Dictionary mapping difficulty levels to their completion status
    """

    ranked_difficulties: list[tuple[Literal["easy", "medium", "hard"], float]] = Field(
        ..., description="Ordered list of difficulty rankings"
    )
    difficulty_status: dict[
        Literal["easy", "medium", "hard"], Literal["incomplete", "completed"]
    ] = Field(..., description="Completion status for each difficulty level")


class RecommendationEngineConfig(BaseModel):
    database_name: str
    collection_name: str
    category: str
    examination_level: str
    academic_class: str
    topic: str
    user_id: int
    topic_id: int


class RecommendationQuestionMetadata(BaseModel):
    """
    Pydantic model for the recommendation question metadata format.

    Attributes:
        category (str): The category of the question, e.g., 'Mathematics', 'Science'.
        topic (str): The specific topic under the category, e.g., 'Algebra', 'Physics'.
        examination_level (str): The examination level, e.g., 'MSCE', 'JCE'.
        academic_class (str): The academic class, e.g., 'Form1', 'Grade 12'.
        difficulty (str): The difficulty level of the question, e.g., 'easy', 'medium', 'hard'.
    """

    category: constr(min_length=1, max_length=255)
    topic: constr(min_length=1, max_length=255)
    examination_level: str
    academic_class: constr(min_length=1, max_length=255)
    difficulty: Literal["easy", "medium", "hard", None]

    class Config:
        """Pydantic configuration."""

        use_enum_values = True  # Ensure Enum or Literal values are used directly
        anystr_strip_whitespace = (
            True  # Automatically strip whitespace from string fields
        )
        validate_assignment = True  # Allow runtime validation on assignment
