from ai_core.learning_mode_rules import LearningModeType, LearningRuleFactory


class ModeMessageGenerator:
    @staticmethod
    def get_message(current_mode: str, difficulty_levels: int) -> str:
        try:
            mode_enum = LearningModeType(current_mode.lower())  # Convert string to enum
        except ValueError:
            raise ValueError(f"Invalid learning mode: {current_mode}")

        rule = LearningRuleFactory.create_rule(mode_enum)

        if mode_enum == LearningModeType.MASTERED:
            return "You've mastered all difficulty levels! Practice with unlimited questions at any time."

        required_correct = int(rule.pass_requirement * rule.questions_per_difficulty * difficulty_levels)
        total_questions = rule.questions_per_difficulty * difficulty_levels

        return f"To advance, correctly answer at least {required_correct} out of {total_questions} questions."
