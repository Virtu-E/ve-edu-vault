from typing import Dict, List

from pydantic import BaseModel, Field, constr
from typing_extensions import Literal


class PerformanceStats(BaseModel):
    """
    Stores comprehensive performance statistics.

    Attributes:
        ranked_difficulties: A list of difficulty rankings ordered by the average number of attempts per difficulty level.
        difficulty_status: A dictionary mapping each difficulty level to its completion status.
    """

    ranked_difficulties: List[tuple[Literal["easy", "medium", "hard"], float]] = Field(
        ...,
        description=(
            "A list of tuples where each tuple contains a difficulty level (easy, medium, hard) "
            "and the corresponding average number of attempts for that difficulty, "
            "ordered by the average attempts in ascending order."
        ),
    )

    difficulty_status: Dict[
        Literal["easy", "medium", "hard"], Literal["incomplete", "completed"]
    ] = Field(
        ...,
        description=(
            "A dictionary mapping each difficulty level to its completion status. "
            "'incomplete' means the user has not yet completed questions for that difficulty, "
            "while 'completed' means they have completed all required questions for that difficulty."
        ),
    )

    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)
    #
    #     # Ensure ranked_difficulties is ordered by average attempts
    #     self.ranked_difficulties.sort(key=lambda x: x[1])


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
