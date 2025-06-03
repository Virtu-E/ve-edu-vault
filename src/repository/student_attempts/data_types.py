from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Attempt(BaseModel):
    """Represents a single student attempt on a question."""

    is_correct: bool
    score: float
    timestamp: datetime

    # Additional fields can be added as needed
    # These fields will be made optional with default=None
    response_data: Optional[Dict[str, Any]] = None
    response_text: Optional[str] = None
    attempt_number: Optional[int] = None

    model_config = ConfigDict(
        extra="ignore"  # Allow extra fields without validation errors
    )


class StudentQuestionAttempt(BaseModel):
    """
    Tracks a student's complete history with a specific question.
    Updated for Pydantic v2 compatibility.
    """

    # Define ID fields to accept both ObjectId and str
    id: str = Field(alias="_id")
    user_id: Union[str, int]  # Accept both string and int
    question_id: str
    question_type: str

    # Topic metadata
    topic: str
    sub_topic: str
    learning_objective: str

    # Summary statistics
    total_attempts: int
    best_score: float
    latest_score: float
    mastered: bool
    first_attempt_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None

    # Array of all attempts
    attempts: List[Attempt]

    # Configuration for Pydantic v2
    model_config = ConfigDict(
        populate_by_field_name=True, extra="ignore"  # Ignore extra fields
    )

    # Pre-processing validator to handle ObjectId and type conversions
    @model_validator(mode="before")
    @classmethod
    def preprocess_data(cls, data):
        """Convert ObjectId to string and handle other type conversions."""
        if isinstance(data, dict):
            # Convert ObjectId to string for id fields
            if "_id" in data and isinstance(data["_id"], ObjectId):
                data["_id"] = str(data["_id"])
            if "question_id" in data and isinstance(data["question_id"], ObjectId):
                data["question_id"] = str(data["question_id"])

            # Ensure user_id is a string if it's an int
            if "user_id" in data and isinstance(data["user_id"], int):
                data["user_id"] = str(data["user_id"])

        return data
