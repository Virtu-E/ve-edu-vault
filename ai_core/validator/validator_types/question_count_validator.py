from typing import Union, Dict

from pydantic import ValidationError

from ai_core.learning_mode_rules import LearningRuleFactory, LearningModeType
from ai_core.validator.base_validator import BaseValidator
from course_ware.models import UserQuestionAttempts


class PrerequisiteQuestionCountValidator(BaseValidator):
    """Validates that the number of questions matches the required count for each difficulty level."""

    def __init__(self, user_question_attempt_instance: UserQuestionAttempts):
        """
        Initialize the validator with user attempt instance and required question count.

        Args:
            user_question_attempt_instance: Instance of UserQuestionAttempts
            required_questions: Number of questions required per difficulty
        """
        if not isinstance(user_question_attempt_instance, UserQuestionAttempts):
            raise ValueError("Invalid user question attempt instance provided")
        self.attempt_instance = user_question_attempt_instance

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
