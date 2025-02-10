from abc import ABC, abstractmethod
from typing import List

from ai_core.learning_mode_rules import BaseLearningModeRule
from data_types.ai_core import LearningHistory, QuestionPromptGeneratorConfig
from repository.ai_core.prompt_engine import PromptEngineRepositoryInterface


class QuestionPromptGeneratorInterface(ABC):
    @abstractmethod
    def generate_question_prompt(self) -> str:
        """
        Generate a formatted question prompt based on the implemented logic.

        Returns:
            str: A formatted question prompt string.
        """
        raise NotImplementedError


class BaseQuestionPromptGenerator(QuestionPromptGeneratorInterface):
    def __init__(
        self,
        rule: BaseLearningModeRule,
        learning_history: LearningHistory,
        repository: PromptEngineRepositoryInterface,
        question_ids: List[str],
        config: QuestionPromptGeneratorConfig,
        failed_difficulties: List[str],
    ):
        """
        Initialize the BaseQuestionPromptGenerator with required dependencies and configuration.

        Args:
            rule (BaseLearningModeRule): Rule that drives the learning mode-specific context.
            learning_history (LearningHistory): User's learning history data.
            repository (PromptEngineRepositoryInterface): Repository to fetch question bank data.
            question_ids (List[str]): List of question IDs to avoid duplicates.
            config (QuestionPromptGeneratorConfig): Configuration for generating the prompt.
            failed_difficulties (List[str]): List of difficulties where the user previously failed.
        """
        self.rule = rule
        self.learning_history = learning_history
        self.repository = repository
        self.question_ids = question_ids
        self.config = config
        self.validate_prerequisite()
        self.failed_difficulties = failed_difficulties

    def validate_prerequisite(self):
        """
        Validate if the required prerequisite mode exists in the learning history.

        Raises:
            ValueError: If the prerequisite mode is missing in the learning history.
        """
        if self.rule.prerequisite and not self.learning_history.modeHistory.get(
            self.rule.prerequisite
        ):
            raise ValueError(
                f"Learning history does not contain the required prerequisite: {self.rule.prerequisite}"
            )

    def generate_question_prompt(self) -> str:
        """
        Generate a formatted question prompt based on the learning mode rule, user history, and configuration.

        Returns:
            str: A dynamically generated question prompt string.
        """
        # Get the template from the rule
        template = self.rule.get_prompt_template()

        # Extract failed difficulties and tags from learning history
        failed_difficulties = self.failed_difficulties
        failed_tags = self.learning_history.get_failed_tags(self.rule.prerequisite)
        previous_attempt_ids = self.question_ids

        # Format mode-specific context
        mode_context = self.rule.mode_specific_context.format(
            failed_difficulties=failed_difficulties,
            failed_tags=failed_tags,
            previous_attempt_ids=previous_attempt_ids,
        )

        course_name = self.config.course_name
        syllabus = self.config.syllabus
        topic_name = self.config.topic_name
        category = self.config.category
        academic_level = self.config.academic_level
        user_learning_history = self.learning_history.model_dump()
        question_bank = self.repository.get_question_bank(self.question_ids)

        # Format the complete prompt
        prompt = template.format(
            course_name=course_name,
            current_mode=self.rule.current_mode,
            mode_description=self.rule.mode_description,
            category=category,
            syllabus=syllabus,
            topic_name=topic_name,
            academic_level=academic_level,
            user_learning_history=user_learning_history,
            mode_specific_context=mode_context,
            mode_specific_task=self.rule.mode_specific_task,
            question_bank=question_bank,
            format_instructions=self.rule.system_template,
        )

        return prompt
