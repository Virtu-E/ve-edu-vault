from typing import Dict, Union

from pydantic import ValidationError

from ai_core.learning_mode_rules import LearningModeType, LearningRuleFactory
from ai_core.validator.base_validator import BaseValidator
from course_ware.models import UserQuestionAttempts


class PrerequisiteQuestionCountValidator(BaseValidator):
    """Validates that the number of questions matches the required count for each difficulty level."""

    def __init__(self, **kwargs):
        """Initialize the validator with kwargs.

        Args:
            **kwargs: Keyword arguments containing user_question_attempt_instance
        """
        attempt_instance = kwargs.get("user_question_attempt_instance")

        if not attempt_instance:
            raise ValueError("user_question_attempt_instance not provided in kwargs")

        if not isinstance(attempt_instance, UserQuestionAttempts):
            raise ValueError(f"Expected UserQuestionAttempts instance, got {type(attempt_instance)}")

        self.attempt_instance = attempt_instance

    def validate(self) -> Union[bool, str]:
        """Validates that each difficulty has the required number of questions.

        Returns:
            Union[bool, str]: True if validation passes, error message string if fails
        """
        try:
            rule_mapping = {
                "normal": LearningModeType.NORMAL,
                "reinforcement": LearningModeType.REINFORCEMENT,
                "recovery": LearningModeType.RECOVERY,
                "reset": LearningModeType.RESET,
                "mastered": LearningModeType.MASTERED,
            }

            current_learning_mode = self.attempt_instance.current_learning_mode
            rule = LearningRuleFactory.create_rule(rule_mapping.get(current_learning_mode))
            version_content = self.attempt_instance.get_latest_question_metadata
            required_questions = rule.questions_per_difficulty

            # Group questions by difficulty
            questions_by_difficulty: Dict[str, list] = {}

            for question_id, entry in version_content.items():
                difficulty = entry.get("difficulty")
                if not difficulty:
                    return f"Missing difficulty for question {question_id}"

                if difficulty not in questions_by_difficulty:
                    questions_by_difficulty[difficulty] = []
                questions_by_difficulty[difficulty].append(question_id)

            # Check if each difficulty has the required number of questions
            for difficulty, questions in questions_by_difficulty.items():
                actual_count = len(questions)
                if actual_count != required_questions:
                    return f"Invalid number of questions for {difficulty} difficulty. Expected {required_questions} questions, but got {actual_count}."

            return True

        except ValidationError as e:
            return f"Schema validation error: {str(e)}"
        except Exception as e:
            return f"Validation error: {str(e)}"
