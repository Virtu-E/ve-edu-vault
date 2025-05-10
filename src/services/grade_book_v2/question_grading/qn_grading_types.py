from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class AttemptedAnswer:
    question_type: Any
    question_metadata: Dict[str, Any]


@dataclass
class Feedback:
    message: str
    explanation: Optional[str] = None
    steps: Optional[List[str]] = None
    hint: Optional[str] = None
    show_solution: bool = False
    misconception: Optional[str] = None


@dataclass
class GradingResponse:
    question_metadata: Dict[str, Any]
    success: bool
    is_correct: bool
    score: float
    feedback: Feedback
    attempts_remaining: int
    question_type: Optional[str] = None

    def to_dict(self):
        data_dict = asdict(self)
        return data_dict


@dataclass
class GradingRequest:
    question_id: str
    user_id: str
    attempted_answer: AttemptedAnswer
