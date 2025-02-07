import json
from abc import ABC, abstractmethod
from typing import Dict

from decouple import config
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

from ai_core.ai.prompt_generators.lang_chain_prompt_generator import (
    LangChainPromptGeneratorInterface,
)


class AIEngineInterface(ABC):
    @abstractmethod
    def get_ai_recommendation(self):
        raise NotImplementedError


class EduAIEngine(AIEngineInterface):
    def __init__(
        self,
        prompt_generator: LangChainPromptGeneratorInterface,
        llm=ChatOpenAI(
            temperature=0.7,
            openai_api_key=config("OPENAI_API_KEY"),
            model="gpt-4",
        ),
    ):
        self.llm = llm
        self.prompt_generator = prompt_generator
        self.output_parser = self._create_output_parser()

    @staticmethod
    def _create_output_parser():
        question_schema = ResponseSchema(
            name="generated_questions",
            description="Array of questions with metadata",
            type="array",
        )
        return StructuredOutputParser.from_response_schemas([question_schema])

    def get_ai_recommendation(self) -> Dict:
        """
        Get AI recommendations using the schema parser
        Returns:
            Dict: Parsed questions with metadata
        """
        messages = self.prompt_generator.generate_ai_prompt()
        response = self.llm(messages)

        try:
            # First parse the content to ensure it's a valid JSON
            # if isinstance(response.content, str):
            #     json_content = json.loads(response.content)
            # else:
            #     json_content = response.content

            # # Format the response to match the schema
            # formatted_response = {"generated_questions": json_content}
            #
            # # Convert back to string for the parser
            # formatted_str = json.dumps(formatted_response)
            #
            # # Parse using the schema
            # parsed_output = self.output_parser.parse(formatted_str)

            return response

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse response content: {e}")
        except Exception as e:
            raise ValueError(f"Error processing response: {e}")
