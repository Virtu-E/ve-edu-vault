from typing import Protocol


class LearningModeStrategy(Protocol):
    """Interface for learning mode strategies - Open/Closed Principle"""

    def get_next_mode(self, current_mode: str, has_failed: bool) -> str:
        """Determine the next learning mode"""
        pass

    def get_guidance_message(self, mode: str) -> str:
        """Get guidance message for the mode"""
        pass


class StandardLearningModeStrategy:
    """Concrete implementation of learning mode strategy"""

    def __init__(self):
        self.mode_progression = {
            "normal": "reinforcement",
            "reinforcement": "recovery",
            "recovery": "reset",
            "reset": "reset",
            "mastered": "mastered",
        }

        self.guidance_messages = {
            "normal": "Answer the required number of questions to level up and progress through the course.",
            "reinforcement": "Focus on completing questions in areas where you had difficulty.",
            "recovery": "Take time to review the fundamental concepts.",
            "reset": "Start fresh with a comprehensive review.",
            "mastered": "Continue practicing to maintain mastery.",
        }

    def get_next_mode(self, current_mode: str, has_failed: bool) -> str:
        if current_mode == "mastered":
            return "mastered"
        return self.mode_progression[current_mode] if has_failed else "mastered"

    def get_guidance_message(self, mode: str) -> str:
        return self.guidance_messages.get(mode)
