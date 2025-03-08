from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, TypeAlias


class DifficultyEnum(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class CompletionStatusEnum(Enum):
    INCOMPLETE = "incomplete"
    COMPLETED = "completed"


RankedDifficulty: TypeAlias = List[tuple[DifficultyEnum, float]]
DifficultyCompletion: TypeAlias = Dict[DifficultyEnum, CompletionStatusEnum]
DifficultyScore: TypeAlias = Dict[DifficultyEnum, int]


@dataclass
class PerformanceStatsData:
    """
    Base model for the performance stats data

    Attributes:
        ranked_difficulties: A list of difficulty rankings ordered by the average number
                            of attempts per difficulty level.
        difficulty_completion: A dictionary mapping each difficulty level to
                           its completion status.
        difficulty_scores: A dictionary containing the number of correct answers
                          for each difficulty level.

    Example data :
      TODO : include example sample data here
    """

    ranked_difficulties: RankedDifficulty
    difficulty_completion: DifficultyCompletion
    difficulty_scores: DifficultyScore

    @property
    def failed_difficulties(self) -> List[DifficultyEnum]:
        """
        Returns a list of difficulty levels that are marked as incomplete.

        Returns:
            List[DifficultyEnum]: A list of difficulty levels that are incomplete.
        """
        return [
            difficulty
            for difficulty, status in self.difficulty_completion.items()
            if status == CompletionStatusEnum.INCOMPLETE
        ]

    @property
    def passed_difficulties(self) -> List[DifficultyEnum]:
        """
        Returns a list of difficulty levels that are marked as completed.

        Returns:
            List[DifficultyEnum]: A list of difficulty levels that are completed.
        """
        return [
            difficulty
            for difficulty, status in self.difficulty_completion.items()
            if status == CompletionStatusEnum.COMPLETED
        ]
