from abc import ABC
from enum import Enum
from typing import Union


class LearningModeType(str, Enum):
    NORMAL = "normal"
    REINFORCEMENT = "reinforcement"
    RECOVERY = "recovery"
    RESET = "reset"
    MASTERED = "mastered"

    @classmethod
    def from_string(cls, value: Union[str, "LearningModeType"]) -> "LearningModeType":
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise ValueError(f"Value must be a string or {cls.__name__}, got {type(value)}")

        try:
            # Try to match the exact enum value first
            return cls(value.lower())
        except ValueError:
            # If no exact match, try to match case-insensitive
            valid_values = {member.value.lower(): member for member in cls}
            if value.lower() in valid_values:
                return valid_values[value.lower()]

            raise ValueError(f"Invalid {cls.__name__}: '{value}'. Valid values are: {', '.join(member.value for member in cls)}")


class BaseLearningModeRule(ABC):
    questions_per_difficulty = 0
    required_correct_questions = 0
    pass_requirement = 0
    attempts_allowed = 0
    prerequisite = ""
    system_template = """You are an intelligent learning assistant tasked with recommending questions and creating learning paths for students.
    Your recommendations should be based on the provided data which includes:

    1. Course Data:
       - All information provided in the Context section (Course details, Mode, Topic, etc.)
       - Any relevant syllabus or curriculum information

    2. Student Data:
       - Learning history and performance metrics
       - Previous attempts and outcomes
       - Failed difficulty levels and tags

    3. Task Requirements:
       - Specific requirements defined in mode_specific_task
       - General requirements (conceptual progression, addressing weaknesses)

    IMPORTANT: When selecting questions:
    1. First check if suitable questions exist in the Question Bank that:
       - Meet all requirements specified in the provided data
       - Haven't been previously attempted (check Previous Attempt IDs)

    2. Your response must always be in this format:
       {
         "question_bank_ids": [],      # List of question IDs from the bank that meet requirements
         "generated_questions": []      # List of newly generated questions only if needed
       }

    3. Only generate new questions if:
       - The questions in the bank have already been answered by the user
       - OR there aren't enough suitable questions in the bank meeting the requirements
       - Use this format for generated questions:
          dict (

        "text": "question_text",
        "difficulty": "difficulty_level",
        "tags": ["tag1", "tag2"],
        "choices": [dict ("text": "option_text", "is_correct": boolean )],
        "solution": dict("explanation": "explanation", "steps": ["step1", "step2"]),
        "hint": "hint_text",
        "metadata": dict("created_by": "model", "time_estimate": dict("minutes": "3"))

    )
        where dict is a dictionary format, i.e. curly braces


    Analyze all provided data to make appropriate recommendations following the specified requirements.
    Provide your response in JSON format with both question_bank_ids and generated_questions arrays, even if one is empty.
    """
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
    - Build conceptual progression
    - Address specific areas of weakness

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
    system_template = """
    You are an intelligent learning assistant that recommends educational resources to support student learning.
    Analyze the student's context, performance history, and learning needs to suggest targeted learning materials.
    Recommend a mix of videos, articles, interactive tools, and other educational content that align with the topic and learning objectives.
    Provide your response in a structured format that can be parsed into JSON with fields for resource type, title, description, difficulty level, and estimated completion time.
    """
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
