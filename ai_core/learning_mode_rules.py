from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional, Type


class LearningModeType(Enum):
    """Learning mode type"""

    NORMAL = "normal"
    REINFORCEMENT = "reinforcement"
    RECOVERY = "recovery"
    RESET = "reset"
    MASTERED = "mastered"


class BaseLearningModeRule(ABC):
    """Abstract base class defining the interface for all learning mode rules"""

    # Common base template that all modes share
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

    # Default system template
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

    @property
    @abstractmethod
    def questions_per_difficulty(self) -> int:
        """Number of questions per difficulty level"""
        pass

    @property
    @abstractmethod
    def required_correct_questions(self) -> int:
        """Number of correct questions required to pass"""
        pass

    @property
    @abstractmethod
    def pass_requirement(self) -> float:
        """Fraction of questions that must be answered correctly to pass"""
        pass

    @property
    @abstractmethod
    def attempts_allowed(self) -> int:
        """Number of attempts allowed (-1 for infinite)"""
        pass

    @property
    @abstractmethod
    def prerequisite(self) -> Optional[LearningModeType]:
        """Prerequisite learning mode (if any)"""
        pass

    @property
    @abstractmethod
    def mode_type(self) -> LearningModeType:
        """The learning mode type this rule applies to"""
        pass

    @property
    def mode_description(self) -> str:
        """Description of the learning mode"""
        return ""

    @property
    def mode_specific_context(self) -> str:
        """Mode-specific context template"""
        return ""

    @property
    def mode_specific_task(self) -> str:
        """Mode-specific task template"""
        return ""

    def get_prompt_template(self) -> str:
        """Returns the prompt template for this learning mode"""
        return self.base_prompt_template


class NormalRule(BaseLearningModeRule):
    """Rule implementation for Normal learning mode"""

    @property
    def questions_per_difficulty(self) -> int:
        return 3

    @property
    def required_correct_questions(self) -> int:
        return 2

    @property
    def pass_requirement(self) -> float:
        return 2 / 3

    @property
    def attempts_allowed(self) -> int:
        return 1

    @property
    def prerequisite(self) -> Optional[LearningModeType]:
        return None

    @property
    def mode_type(self) -> LearningModeType:
        return LearningModeType.NORMAL

    @property
    def mode_specific_context(self) -> str:
        return """
        Failed Difficulty Levels: {failed_difficulties}
        Failed Tags: {failed_tags}
        Previous Attempt IDs: {previous_attempt_ids}
        """

    @property
    def mode_specific_task(self) -> str:
        return """
        Task:
        Select 3 questions for each failed difficulty level where:
        - 60% focus on failed tags
        - 40% introduce new but related tags
        """


class RecoveryRule(BaseLearningModeRule):
    """Rule implementation for Recovery learning mode"""

    @property
    def questions_per_difficulty(self) -> int:
        return 5

    @property
    def required_correct_questions(self) -> int:
        return 4

    @property
    def pass_requirement(self) -> float:
        return 4 / 5

    @property
    def attempts_allowed(self) -> int:
        return 2

    @property
    def prerequisite(self) -> Optional[LearningModeType]:
        return LearningModeType.REINFORCEMENT

    @property
    def mode_type(self) -> LearningModeType:
        return LearningModeType.NORMAL

    @property
    def mode_specific_context(self) -> str:
        return """
        Failed Difficulty Levels: {failed_difficulties}
        Failed Tags: {failed_tags}
        Previous Attempt IDs: {previous_attempt_ids}
        """

    @property
    def mode_specific_task(self) -> str:
        return """
        Task:
        Select 5 questions for each failed difficulty level where:
        - 60% focus on failed tags
        - 40% introduce new but related tags
        """


class ReinforcementRule(BaseLearningModeRule):
    """Rule implementation for Reinforcement learning mode"""

    @property
    def questions_per_difficulty(self) -> int:
        return 3

    @property
    def required_correct_questions(self) -> int:
        return 3

    @property
    def pass_requirement(self) -> float:
        return 3 / 3

    @property
    def attempts_allowed(self) -> int:
        return 1

    @property
    def prerequisite(self) -> Optional[LearningModeType]:
        return LearningModeType.RECOVERY

    @property
    def mode_type(self) -> LearningModeType:
        return LearningModeType.REINFORCEMENT

    @property
    def mode_specific_context(self) -> str:
        return """
        Failed Difficulty Levels: {failed_difficulties}
        Failed Tags: {failed_tags}
        Previous Attempt IDs: {previous_attempt_ids}
        """

    @property
    def mode_specific_task(self) -> str:
        return """
        Task:
        Select 3 questions for each failed difficulty level where:
        - 60% focus on failed tags
        - 40% introduce new but related tags
        """


class ResetRule(BaseLearningModeRule):
    """Rule implementation for Reset learning mode"""

    @property
    def questions_per_difficulty(self) -> int:
        return 3

    @property
    def required_correct_questions(self) -> int:
        return 3

    @property
    def pass_requirement(self) -> float:
        return 3 / 3

    @property
    def attempts_allowed(self) -> int:
        return -1  # infinite attempts allowed

    @property
    def prerequisite(self) -> Optional[LearningModeType]:
        return LearningModeType.REINFORCEMENT

    @property
    def mode_type(self) -> LearningModeType:
        return LearningModeType.RESET

    @property
    def mode_specific_context(self) -> str:
        return """
        Failed Difficulty Levels: {failed_difficulties}
        Failed Tags: {failed_tags}
        Previous Attempt IDs: {previous_attempt_ids}
        """

    @property
    def mode_specific_task(self) -> str:
        return """
        Task:
        Select 3 questions for each failed difficulty level where:
        - 60% focus on failed tags
        - 40% introduce new but related tags
        """


class MasteredRule(BaseLearningModeRule):
    """Rule implementation for Mastered learning mode"""

    @property
    def questions_per_difficulty(self) -> int:
        return -1  # infinite

    @property
    def required_correct_questions(self) -> int:
        return 0

    @property
    def pass_requirement(self) -> float:
        return 0

    @property
    def attempts_allowed(self) -> int:
        return -1  # infinite attempts allowed

    @property
    def prerequisite(self) -> Optional[LearningModeType]:
        return None

    @property
    def mode_type(self) -> LearningModeType:
        return LearningModeType.MASTERED


class LearningRuleFactory:
    """Factory for creating learning mode rules"""

    # Cache rules to avoid recreating them
    _rules: Dict[LearningModeType, BaseLearningModeRule] = {}

    # Map of mode types to rule classes
    _rule_classes: Dict[LearningModeType, Type[BaseLearningModeRule]] = {
        LearningModeType.NORMAL: NormalRule,
        LearningModeType.REINFORCEMENT: ReinforcementRule,
        LearningModeType.RECOVERY: RecoveryRule,
        LearningModeType.RESET: ResetRule,
        LearningModeType.MASTERED: MasteredRule,
    }

    @classmethod
    def get_rule(cls, mode: LearningModeType) -> BaseLearningModeRule:
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
            raise ValueError(
                f"Mode must be a LearningModeType or string, got {type(mode)}"
            )

        # Return cached instance if available
        if mode in cls._rules:
            return cls._rules[mode]

        # Get the rule class
        if mode not in cls._rule_classes:
            raise ValueError(f"Unsupported learning mode: {mode}")

        rule_class = cls._rule_classes[mode]

        # Create and cache the rule
        rule = rule_class()
        cls._rules[mode] = rule

        return rule
