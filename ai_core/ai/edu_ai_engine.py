from abc import ABC, abstractmethod
from typing import Dict

from decouple import config
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

from ai_core.ai.prompt_generators.lang_chain_prompt_generator import LangChainPromptGeneratorInterface


class AIEngineInterface(ABC):
    @abstractmethod
    def get_ai_recommendation(self):
        raise not NotImplementedError


class EduAIEngine(AIEngineInterface):
    def __init__(self, prompt_generator: LangChainPromptGeneratorInterface, llm=ChatOpenAI(temperature=0.7, openai_api_key=config("OPENAI_API_KEY"))):
        self.llm = llm
        self.prompt_generator = prompt_generator
        self.output_parser = self._create_output_parser()

    @staticmethod
    def _create_output_parser():
        question_schema = ResponseSchema(name="generated_questions", description="Array of questions with metadata", type="array")
        return StructuredOutputParser.from_response_schemas([question_schema])

    def get_ai_recommendation(self) -> Dict:
        messages = self.prompt_generator.generate_ai_prompt()
        response = self.llm(messages)
        return self.output_parser.parse(response.content)
