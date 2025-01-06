import pytest

from ai_core.performance_calculators import AttemptBasedDifficultyRankerCalculator
from course_ware.tests.course_ware_factory import QuestionMetadataFactory


@pytest.fixture
def calculator():
    return AttemptBasedDifficultyRankerCalculator()


@pytest.fixture
def empty_question_data():
    return {}


@pytest.fixture
def completed_easy_questions():
    """Generate a set of easy questions with high completion rate"""
    return {
        f"q{i}": QuestionMetadataFactory(
            difficulty="easy", is_correct="true", attempt_number=1
        )
        for i in range(5)
    }


@pytest.fixture
def incomplete_medium_questions():
    """Generate a set of medium questions with low completion rate"""
    return {
        f"q{i}": QuestionMetadataFactory(
            difficulty="medium", is_correct="false", attempt_number=3
        )
        for i in range(5)
    }


@pytest.fixture
def mixed_hard_questions():
    """Generate a set of hard questions with mixed completion"""
    questions = {}
    # 2 correct answers
    for i in range(2):
        questions[f"hard_correct_{i}"] = QuestionMetadataFactory(
            difficulty="hard", is_correct="true", attempt_number=3
        )
    # 4 incorrect answers
    for i in range(4):
        questions[f"hard_incorrect_{i}"] = QuestionMetadataFactory(
            difficulty="hard", is_correct="false", attempt_number=2
        )
    return questions
