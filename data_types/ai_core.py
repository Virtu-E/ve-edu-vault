from typing import Dict, List

from pydantic import BaseModel, Field
from pydantic.v1 import validator
from typing_extensions import Literal

DifficultyLiteral = Literal["easy", "medium", "hard"]
LearningMode = Literal["normal", "reinforcement", "recovery", "reset", "mastered"]


class RecommendationEngineConfig(BaseModel):
    database_name: str
    collection_name: str
    category: str
    examination_level: str
    academic_class: str
    topic: str
    user_id: int
    topic_id: int


class Attempt(BaseModel):
    success: bool
    timeSpent: int  # in minutes
    attemptNumber: int


class QuestionAIContext(BaseModel):
    id: str = Field(..., alias="_id")
    difficulty: str
    tags: List[str]
    attempts: Attempt


class DifficultyStats(BaseModel):
    totalAttempts: int
    successRate: float
    averageTime: float
    failedTags: List[str]

    # Attempt-based stats
    firstAttemptSuccessRate: float  # Success rate on first attempts
    secondAttemptSuccessRate: float  # Success rate on second attempts
    thirdAttemptSuccessRate: float  # Success rate on third attempts
    averageAttemptsToSuccess: float  # Average number of attempts needed for success

    # Completion stats
    completionRate: float  # Percentage of questions completed successfully
    incompleteRate: float  # Percentage of questions not completed after all attempts
    earlyAbandonment: (
        float  # Percentage of questions abandoned before using all attempts
    )

    # Time-based stats
    averageFirstAttemptTime: float  # Average time spent on first attempts
    averageSecondAttemptTime: float  # Average time spent on second attempts
    averageThirdAttemptTime: float  # Average time spent on third attempts
    timeDistribution: Dict[str, float]  # Distribution of time spent across attempts


class ModeData(BaseModel):
    questions: List[QuestionAIContext]
    difficultyStats: Dict[str, DifficultyStats]


class LearningDefaults(BaseModel):
    userId: int
    block_id: str
    modeHistory: Dict[LearningMode, List[ModeData]]

    model_config = {"json_schema_extra": {"examples": [{}]}}


class LearningHistory(LearningDefaults):
    """
    Tracks a user's learning history including question attempts and difficulty statistics.
    Can include data for normal, reinforcement, mastered , reset and recovery modes.
    """

    modeHistory: Dict[LearningMode, List[ModeData]]  # Must have at least one mode

    model_config = {"extra": "forbid"}

    @property
    def active_modes(self) -> List[LearningMode]:
        """Returns a list of active learning modes in the history"""
        return list(self.modeHistory.keys())

    def get_failed_tags(self, mode: LearningMode) -> Dict[str, List[str]]:
        failed_tags = {}
        for mode_data in self.modeHistory.get(mode, []):
            for difficulty, stats in mode_data.difficultyStats.items():
                if difficulty not in failed_tags:
                    failed_tags[difficulty] = []
                failed_tags[difficulty].extend(
                    tag
                    for tag in stats.failedTags
                    if tag not in failed_tags[difficulty]
                )
        return failed_tags


class QuestionBank(BaseModel):
    text: str
    difficulty: str
    id: str = Field(..., alias="_id")
    tags: list[str]

    class Config:
        allow_population_by_field_name = True

    @validator("_id", pre=True, always=True)
    def ensure_string(cls, value):
        return str(value)


class QuestionPromptGeneratorConfig(BaseModel):
    course_name: str
    topic_name: str
    academic_level: str
    syllabus: str
    category: str


class DifficultyScore(BaseModel):
    difficulty: Literal["easy", "medium", "hard"]
    users_score: str
    status: Literal["success", "failed"]
    required_score: str


class PreviousMode(BaseModel):
    mode_name: str
    mode_guidance: str
    guidance: str
    required_score: int
    passed_difficulties: list[DifficultyScore]
    failed_difficulties: list[DifficultyScore]
    total_questions: int


class NextMode(BaseModel):
    mode_name: str
    mode_guidance: str
    guidance: str
    required_score: int
    total_questions: int


class EvaluationResult(BaseModel):
    status: str
    passed: bool
    next_mode: NextMode
    previous_mode: PreviousMode
