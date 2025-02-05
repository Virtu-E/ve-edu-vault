from unittest.mock import MagicMock, patch
import pytest
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import StructuredOutputParser
from langchain.schema import AIMessage, HumanMessage, SystemMessage

from ai_core.ai.edu_ai_engine import EduAIEngine, AIEngineInterface


class MockLangChainPromptGenerator:
    def generate_ai_prompt(self):
        return [
            SystemMessage(content="Mock system prompt"),
            HumanMessage(content="Mock human message"),
        ]


@pytest.fixture
def mock_prompt_generator():
    """Fixture for the mocked prompt generator."""
    return MockLangChainPromptGenerator()


@pytest.fixture
def mock_llm():
    """Fixture for a mocked ChatOpenAI instance."""
    mock = MagicMock(spec=ChatOpenAI)
    mock.return_value = AIMessage(content='{"generated_questions": [{"question": "What is AI?", "metadata": {}}]}')
    return mock


@pytest.fixture
def edu_ai_engine(mock_prompt_generator, mock_llm):
    """Fixture for the EduAIEngine instance with mocked dependencies."""
    return EduAIEngine(prompt_generator=mock_prompt_generator, llm=mock_llm)


def test_edu_ai_engine_implements_interface():
    """Test that EduAIEngine properly implements AIEngineInterface."""
    assert issubclass(EduAIEngine, AIEngineInterface), "EduAIEngine should implement AIEngineInterface"


def test_create_output_parser():
    """Test the static _create_output_parser method."""
    parser = EduAIEngine._create_output_parser()
    assert isinstance(parser, StructuredOutputParser)

    # Verify the schema structure
    schemas = parser.response_schemas
    assert len(schemas) == 1
    assert schemas[0].name == "generated_questions"
    assert schemas[0].type == "array"


def test_get_ai_recommendation_success(edu_ai_engine, mock_llm):
    """Test successful AI recommendation generation."""
    expected_response = {"generated_questions": [{"question": "What is AI?", "metadata": {}}]}

    mock_llm.return_value = AIMessage(content='{"generated_questions": [{"question": "What is AI?", "metadata": {}}]}')

    result = edu_ai_engine.get_ai_recommendation()

    assert isinstance(result, dict)
    assert result == expected_response
    mock_llm.assert_called_once()


def test_get_ai_recommendation_with_complex_response(edu_ai_engine, mock_llm):
    """Test AI recommendation with more complex response structure."""
    mock_response = """{
        "generated_questions": [
            {
                "question": "What is machine learning?",
                "metadata": {
                    "difficulty": "intermediate",
                    "category": "AI",
                    "tags": ["ML", "AI basics"]
                }
            }
        ]
    }"""
    mock_llm.return_value = AIMessage(content=mock_response)

    result = edu_ai_engine.get_ai_recommendation()

    assert isinstance(result["generated_questions"][0]["metadata"], dict)
    assert "difficulty" in result["generated_questions"][0]["metadata"]
    assert "category" in result["generated_questions"][0]["metadata"]
    assert "tags" in result["generated_questions"][0]["metadata"]


def test_get_ai_recommendation_invalid_json(edu_ai_engine, mock_llm):
    """Test handling of invalid JSON response."""
    mock_llm.return_value = AIMessage(content="Invalid JSON content")

    with pytest.raises(Exception) as exc_info:
        edu_ai_engine.get_ai_recommendation()

    assert "parsing" in str(exc_info.value).lower()


def test_get_ai_recommendation_missing_required_field(edu_ai_engine, mock_llm):
    """Test handling of valid JSON but missing required field."""
    mock_llm.return_value = AIMessage(content='{"wrong_field": []}')

    with pytest.raises(Exception) as exc_info:
        edu_ai_engine.get_ai_recommendation()

    assert "generated_questions" in str(exc_info.value).lower()


def test_prompt_generator_integration(edu_ai_engine, mock_prompt_generator):
    """Test integration with prompt generator."""
    with patch.object(
        mock_prompt_generator,
        "generate_ai_prompt",
        wraps=mock_prompt_generator.generate_ai_prompt,
    ) as mock_generate:
        edu_ai_engine.get_ai_recommendation()

        mock_generate.assert_called_once()
        # Just verify the method was called - the actual message validation
        # is handled in other tests


def test_llm_integration_with_messages(edu_ai_engine, mock_llm, mock_prompt_generator):
    """Test that LLM receives correct message format."""
    edu_ai_engine.get_ai_recommendation()

    mock_llm.assert_called_once()
    args, _ = mock_llm.call_args

    assert isinstance(args[0], list)
    assert len(args[0]) == 2
    assert isinstance(args[0][0], SystemMessage)
    assert isinstance(args[0][1], HumanMessage)
    assert args[0][0].content == "Mock system prompt"


def test_initialization_with_custom_llm(mock_prompt_generator):
    """Test initialization with a custom LLM instance."""
    custom_llm = ChatOpenAI(temperature=0.5, openai_api_key="test_key")
    engine = EduAIEngine(prompt_generator=mock_prompt_generator, llm=custom_llm)
    assert isinstance(engine.llm, ChatOpenAI)
    assert engine.llm.temperature == 0.5
