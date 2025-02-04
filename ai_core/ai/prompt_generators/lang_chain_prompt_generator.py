from abc import ABC, abstractmethod
from typing import List

from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage

from ai_core.ai.prompt_generators.base_prompt_generator import BaseQuestionPromptGenerator
from ai_core.learning_mode_rules import BaseLearningModeRule
from data_types.ai_core import QuestionPromptGeneratorConfig, LearningHistory
from repository.ai_core.prompt_engine import PromptEngineRepositoryInterface


class LangChainPromptGeneratorInterface(ABC):
    @abstractmethod
    def generate_ai_prompt(self) -> List[BaseMessage]:
        """
        Abstract method to generate AI prompts.

        Returns:
            List[BaseMessage]: A list of BaseMessage objects that represent the generated prompts.
        """
        pass


class LangChainQuestionPromptGenerator(BaseQuestionPromptGenerator):
    def __init__(self, reinforcement_rule: BaseLearningModeRule, learning_history: LearningHistory, repository: PromptEngineRepositoryInterface, question_ids: List[str], config: QuestionPromptGeneratorConfig):
        """
        Initializes the LangChainQuestionPromptGenerator.

        Args:
            reinforcement_rule (BaseLearningModeRule): The rule associated with reinforcement learning mode.
            learning_history (LearningHistory): The user's learning history data.
            repository (PromptEngineRepositoryInterface): The repository to fetch question banks or related data.
            question_ids (List[str]): A list of question IDs to include in the question bank.
            config (QuestionPromptGeneratorConfig): Configuration for generating question prompts.
        """
        super().__init__(rule=reinforcement_rule, learning_history=learning_history, repository=repository, question_ids=question_ids, config=config)

    @staticmethod
    def _create_output_parser():
        """
        Creates an output parser for processing generated questions.

        Returns:
            StructuredOutputParser: The structured parser configured to parse arrays of generated questions.
        """
        question_schema = ResponseSchema(name="generated_questions", description="Array of questions with metadata", type="array")
        return StructuredOutputParser.from_response_schemas([question_schema])

    def generate_question_prompt(self) -> List[BaseMessage]:
        """
        Generates a question prompt based on the provided reinforcement rule, learning history, and other configurations.

        Returns:
            List[BaseMessage]: A list consisting of system and human messages to serve as input for the AI model.
        """
        prompt = super().generate_question_prompt()
        return [SystemMessage(content=prompt), HumanMessage(content="Generate content based on the above context and requirements.")]
