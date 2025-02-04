import pytest
from unittest.mock import MagicMock
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import StructuredOutputParser

from ai_core.ai.edu_ai_engine import EduAIEngine


class MockLangChainPromptGenerator:
    def generate_ai_prompt(self):
        return [{"role": "system", "content": "Mock system prompt"}]


@pytest.fixture
def mock_prompt_generator():
    """Fixture for the mocked prompt generator."""
    return MockLangChainPromptGenerator()


@pytest.fixture
def mock_llm():
    """Fixture for a mocked ChatOpenAI instance."""
    mock_chat_open_ai = MagicMock(spec=ChatOpenAI)
    # Mocking the LLM's return response to simulate an LLMResult
    mock_chat_open_ai.return_value = MagicMock(content='{"generated_questions": [{"question": "What is AI?", "metadata": {}}]}')
    return mock_chat_open_ai


@pytest.fixture
def edu_ai_engine(mock_prompt_generator, mock_llm):
    """Fixture for the EduAIEngine instance with mocked dependencies."""
    return EduAIEngine(prompt_generator=mock_prompt_generator, llm=mock_llm)


def test_create_output_parser():
    """Test the static _create_output_parser method."""
    parser = EduAIEngine._create_output_parser()
    assert isinstance(parser, StructuredOutputParser), "Output parser is not of type StructuredOutputParser."


def test_get_ai_recommendation_success(edu_ai_engine, mock_prompt_generator, mock_llm):
    """Test the get_ai_recommendation method for correct behavior."""
    mock_llm.return_value.content = '{"generated_questions": [{"question": "What is AI?", "metadata": {}}]}'

    result = edu_ai_engine.get_ai_recommendation()

    assert isinstance(result, dict), "Result is not a dictionary."
    assert "generated_questions" in result, "Response does not contain 'generated_questions'."
    assert isinstance(result["generated_questions"], list), "'generated_questions' is not a list."
    assert result["generated_questions"][0]["question"] == "What is AI?", "Question value is incorrect."


def test_get_ai_recommendation_invalid_response(edu_ai_engine, mock_prompt_generator, mock_llm):
    """Test the get_ai_recommendation method when the LLM returns invalid content."""
    # Mock the LLM's response to return invalid JSON
    mock_llm.return_value.content = "Invalid response"

    with pytest.raises(AssertionError, match="Error parsing response content"):
        edu_ai_engine.get_ai_recommendation()


def test_integration_with_prompt_generator(mock_prompt_generator, mock_llm):
    """Test if the generate_ai_prompt is called correctly."""
    engine = EduAIEngine(prompt_generator=mock_prompt_generator, llm=mock_llm)

    # Spy on the `generate_ai_prompt` method of the prompt generator
    spy = MagicMock(wraps=mock_prompt_generator.generate_ai_prompt)
    engine.prompt_generator.generate_ai_prompt = spy

    engine.get_ai_recommendation()

    spy.assert_called_once()


def test_integration_with_llm(mock_prompt_generator):
    """Test if the LLM object is used as expected."""
    mock_llm = MagicMock(spec=ChatOpenAI)
    mock_llm.return_value = MagicMock(content='{"generated_questions": [{"question": "Test question", "metadata": {}}]}')
    engine = EduAIEngine(prompt_generator=mock_prompt_generator, llm=mock_llm)

    engine.get_ai_recommendation()

    mock_llm.assert_called_once()

    args, kwargs = mock_llm.call_args
    args, kwargs = mock_llm.call_args
    assert len(args) > 0, "No positional arguments passed to LLM."
    assert isinstance(args[0], list), "Messages were not passed as a list of messages."


def test_output_parser_initialization(mock_prompt_generator):
    """Test if the output_parser gets initialized properly."""
    engine = EduAIEngine(prompt_generator=mock_prompt_generator)
    assert isinstance(engine.output_parser, StructuredOutputParser), "Output parser was not initialized correctly."
