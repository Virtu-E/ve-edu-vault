from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


class QuestionMetadata(BaseModel):
    """
    Schema for a single question metadata entry in the UserQuestionAttempts django model.
    """

    question_id: str  # this is the mongo question ID
    attempt_number: int  # the maximum attempt number will be based on the users current learning mode : (Normal, reinforcement or recovery )
    is_correct: bool
    topic: str
    difficulty: Literal["easy", "medium", "hard"]


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


class CourseSyncResponse(BaseModel):
    status: str
    message: str
    course_id: str
    changes_made: bool
    num_success: int = 0
    num_failed: int = 0
