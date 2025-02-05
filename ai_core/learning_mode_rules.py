from abc import ABC
from enum import Enum


class LearningModeType(Enum):
    NORMAL = "normal"
    REINFORCEMENT = "reinforcement"
    RECOVERY = "recovery"
    RESET = "reset"
    MASTERED = "mastered"


class BaseLearningModeRule(ABC):
    questions_per_difficulty = 0
    required_correct_questions = 0
    pass_requirement = 0
    attempts_allowed = 0
    prerequisite = ""
    system_template = """You are an intelligent learning assistant tasked with recommending questions and creating learning paths for students.
Your recommendations should be based on their current learning mode, performance history, and specific requirements.
Provide your response in a structured format that can be parsed into JSON."""
    current_mode = ""
    mode_specific_context = ""
    mode_description = ""
    mode_specific_task = ""
    base_prompt_template = """
    Context:
    Current Course: {course_name}
    Country: Malawi
    Category : {category}
    CurrentMode: {current_mode}
    ModeDescription: {mode_description}
    Syllabus: {syllabus}
    Current Topic: {topic_name}
    Academic Level: {academic_level}
    User Learning History : {user_learning_history}
    {mode_specific_context}

    {mode_specific_task}

    Requirements:
    - Exclude questions from Previous Attempt IDs
    - Build conceptual progression
    - Address specific areas of weakness
    - If no applicable questions from question bank, generate new questions from the relevant context.

    Return questions in this format:
    [ dict (

        "text": "question_text",
        "difficulty": "difficulty_level",
        "tags": ["tag1", "tag2"],
        "choices": [dict ("text": "option_text", "is_correct": boolean )],
        "solution": dict("explanation": "explanation", "steps": ["step1", "step2"]),
        "hint": "hint_text",
        "metadata": dict("created_by": "model", "time_estimate": dict("minutes": "3"))

    )
    ]

    where dict is a dictionary format, i.e. curly braces

    Question Bank:
    {question_bank}

    {format_instructions}
    """

    def get_prompt_template(self):
        return self.base_prompt_template


class NormalRule(BaseLearningModeRule):
    questions_per_difficulty = 3
    pass_requirement = 2 / 3
    required_correct_questions = 2
    attempts_allowed = 1
    prerequisite = None
    mode_description = ""
    current_mode = LearningModeType.NORMAL
    mode_specific_context = """
     Failed Difficulty Levels: {failed_difficulties}
     Failed Tags: {failed_tags}
     Previous Attempt IDs: {previous_attempt_ids}
     """

    mode_specific_task = """
              Task:
              Select 3 questions for each failed difficulty level where:
              - 60% focus on failed tags
              - 40% introduce new but related tags
              """


class RecoveryRule(BaseLearningModeRule):
    questions_per_difficulty = 5
    pass_requirement = 4 / 5
    required_correct_questions = 4
    current_mode = LearningModeType.RECOVERY
    attempts_allowed = 2
    prerequisite = LearningModeType.REINFORCEMENT
    mode_description = ""
    mode_specific_context = """
       Failed Difficulty Levels: {failed_difficulties}
       Failed Tags: {failed_tags}
       Previous Attempt IDs: {previous_attempt_ids}
       """

    mode_specific_task = """
       Task:
       Select 5 questions for each failed difficulty level where:
       - 60% focus on failed tags
       - 40% introduce new but related tags
       """


class ReinforcementRule(BaseLearningModeRule):
    questions_per_difficulty = 3
    pass_requirement = 3 / 3
    required_correct_questions = 3
    attempts_allowed = 1
    current_mode = LearningModeType.REINFORCEMENT
    prerequisite = LearningModeType.NORMAL
    mode_description = ""
    mode_specific_context = """
    Failed Difficulty Levels: {failed_difficulties}
    Failed Tags: {failed_tags}
    Previous Attempt IDs: {previous_attempt_ids}
    """

    mode_specific_task = """
    Task:
    Select 3 questions for each failed difficulty level where:
    - 60% focus on failed tags
    - 40% introduce new but related tags
    """


class ResetRule(BaseLearningModeRule):
    questions_per_difficulty = 3
    pass_requirement = 3 / 3
    required_correct_questions = 3
    attempts_allowed = -1  # infinite attempts allowed
    prerequisite = LearningModeType.RECOVERY
    mode_description = ""
    current_mode = LearningModeType.RESET
    system_template = """You are an intelligent learning assistant that recommends educational resources to support student learning.
    Analyze the student's context, performance history, and learning needs to suggest targeted learning materials.
    Recommend a mix of videos, articles, interactive tools, and other educational content that align with the topic and learning objectives.
    Provide your response in a structured format that can be parsed into JSON with fields for resource type, title, description, difficulty level, and estimated completion time."""
    mode_specific_context = """
          Failed Difficulty Levels: {failed_difficulties}
          Failed Tags: {failed_tags}
          Previous Attempt IDs: {previous_attempt_ids}
          """

    mode_specific_task = """
          Task:
          Select 3 questions for each failed difficulty level where:
          - 60% focus on failed tags
          - 40% introduce new but related tags
          """


class MasteredRule(BaseLearningModeRule):
    questions_per_difficulty = -1  # infinite
    required_correct_questions = 0
    pass_requirement = 0
    current_mode = LearningModeType.MASTERED
    attempts_allowed = -1  # infinite attempts allowed
    prerequisite = None


class LearningRuleFactory:
    """A simple factory for creating learning mode rules"""

    @staticmethod
    def create_rule(mode: LearningModeType) -> "BaseLearningModeRule":
        """
        Create and return a rule instance based on the learning mode

        Args:
            mode: The learning mode to create a rule for

        Returns:
            An instance of the appropriate rule class

        Raises:
            ValueError: If an invalid mode is provided
        """
        if not isinstance(mode, LearningModeType):
            raise ValueError(f"Mode must be a LearningModeType, got {type(mode)}")

        if mode == LearningModeType.NORMAL:
            return NormalRule()
        elif mode == LearningModeType.REINFORCEMENT:
            return ReinforcementRule()
        elif mode == LearningModeType.RECOVERY:
            return RecoveryRule()
        elif mode == LearningModeType.RESET:
            return ResetRule()
        elif mode == LearningModeType.MASTERED:
            return MasteredRule()
        else:
            raise ValueError(f"Unsupported learning mode: {mode}")
