import pytest

from src.services.course_sync import (
    DefaultQuestionSetAssignerMixin,
)


@pytest.fixture
def mixin_instance():
    """Fixture that returns a concrete instance of the DefaultQuestionSetAssignerMixin"""
    return type("ConcreteClass", (DefaultQuestionSetAssignerMixin,), {})()


@pytest.fixture
def sample_questions():
    """Fixture that returns a list of sample questions for testing"""
    return [
        {
            "id": "q1",
        },
        {
            "id": "q2",
        },
        {
            "id": "q3",
        },
    ]


@pytest.fixture
def empty_questions():
    """Fixture that returns an empty questions list"""
    return []


@pytest.fixture
def different_format_questions():
    """Fixture that returns questions in a different format"""
    return [{"question_id": "q1"}, {"question_id": "q2"}]
