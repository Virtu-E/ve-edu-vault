from typing import Literal

from pydantic import BaseModel, Field


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
    user_id: str
    topic_id: str
