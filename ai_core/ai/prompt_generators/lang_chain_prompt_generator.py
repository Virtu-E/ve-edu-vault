from abc import ABC, abstractmethod
from typing import List

from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from ai_core.ai.prompt_generators.base_prompt_generator import BaseQuestionPromptGenerator


class LangChainPromptGeneratorInterface(ABC):
    @abstractmethod
    def generate_ai_prompt(self) -> List[BaseMessage]:
        """
        Abstract method to generate AI prompts.

        Returns:
            List[BaseMessage]: A list of BaseMessage objects that represent the generated prompts.
        """
        pass


class LangChainQuestionPromptGenerator(LangChainPromptGeneratorInterface):
    def __init__(
        self,
        base_prompt: BaseQuestionPromptGenerator,
    ):
        self.base_prompt = base_prompt

    @staticmethod
    def _create_output_parser():
        """
        Creates an output parser for processing generated questions.

        Returns:
            StructuredOutputParser: The structured parser configured to parse arrays of generated questions.
        """
        question_schema = ResponseSchema(
            name="generated_questions",
            description="Array of questions with metadata",
            type="array",
        )
        return StructuredOutputParser.from_response_schemas([question_schema])

    def generate_ai_prompt(self) -> List[BaseMessage]:
        """
        Generates a question prompt based on the provided reinforcement rule, learning history, and other configurations.

        Returns:
            List[BaseMessage]: A list consisting of system and human messages to serve as input for the AI model.
        """
        prompt = self.base_prompt.generate_question_prompt()
        return [
            SystemMessage(content=prompt),
            HumanMessage(content="Generate content based on the above context and requirements."),
        ]
