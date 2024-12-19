import pytest

from ai_core.performance_calculators import PerformanceCalculatorInterface
from ai_core.performance_engine import PerformanceEngine
from ai_core.tests.performance_engine.performance_engine_factory import TopicFactory
from data_types.ai_core import PerformanceStats


class MockPerformanceCalculator(PerformanceCalculatorInterface):
    def calculate_performance(self, question_metadata):
        return PerformanceStats(
            ranked_difficulties=[("easy", 2.6)],
            difficulty_status={
                "easy": "incomplete",
                "hard": "completed",
                "medium": "completed",
            },
        )


@pytest.fixture
def performance_calculator():
    return MockPerformanceCalculator()


@pytest.fixture
def topic():
    return TopicFactory()


@pytest.fixture
def performance_engine(topic, user, performance_calculator):
    return PerformanceEngine(
        topic_id=topic.id,
        user_id=user.id,
        performance_calculator=performance_calculator,
    )
