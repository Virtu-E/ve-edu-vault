from typing import Any, Dict, List, Optional

from pydantic import BaseModel, conint


class QuestionMetadata(BaseModel):
    """
    Schema for a single question metadata entry in the UserQuestionAttempts django model.
    """

    question_id: str  # this is the mongo question ID
    attempt_number: conint(ge=1, le=3)  # Minimum 1, Maximum 3
    is_correct: bool
    topic: str
    difficulty: str


class UserQuestionAttemptsSchema(BaseModel):
    """
    Pydantic model for user question attempts ( UserQuestionAttempts ) django model.
    """

    user_id: int
    topic_id: int
    question_metadata: dict[str, dict[str, QuestionMetadata | Any]]
    # Top-level key: Version (e.g., "v1.0.0")
    # Second-level key: Question ID (e.g., "q123")

    model_config = {"from_attributes": True}


class Block(BaseModel):
    children: List[str]
    complete: bool
    description: Optional[str]
    display_name: Optional[str]
    due: Optional[str]
    effort_activities: Optional[int]
    effort_time: Optional[str]
    icon: Optional[str]
    id: str
    lms_web_url: Optional[str]
    resume_block: bool
    type: Optional[str]
    has_scheduled_content: Optional[bool]
    hide_from_toc: bool


class BlocksData(BaseModel):
    blocks: Dict[str, Block]
