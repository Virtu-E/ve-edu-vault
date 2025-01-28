from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from ai_core.recommendation.recommendation_engine import RecommendationEngine
from course_ware.tests.course_ware_factory import TopicFactory
from data_types.ai_core import RecommendationEngineConfig


@pytest.fixture
def topic():
    return TopicFactory()


@pytest.fixture
def sample_config(user, topic):
    return RecommendationEngineConfig(
        database_name="test_db",
        collection_name="test_collection",
        category="math",
        topic="algebra",
        examination_level="high_school",
        academic_class="10th",
        user_id=user.id,
        topic_id=topic.id,
    )


@pytest.fixture
def mock_performance_engine():
    engine = AsyncMock()
    engine.get_topic_performance_stats.return_value = (
        [("easy", 0.8), ("medium", 0.5), ("hard", 0.2)],
        {"easy": "incomplete", "medium": "completed", "hard": "completed"},
    )
    return engine


@pytest.fixture
def mock_database_engine():
    engine = AsyncMock()
    collection = [
        {
            "_id": f"question_{i}",
            "question_id": f"question_{i}",
            "text": f"Test question {i}",
            "topic": "Mathematics",
            "category": "Algebra",
            "academic_class": "10th Grade",
            "examination_level": "Intermediate",
            "difficulty": "easy",
            "tags": ["math", "algebra", "practice"],
            "choices": [
                {"text": f"Choice {j}", "is_correct": j == 0} for j in range(4)
            ],
            "solution": {
                "explanation": f"Explanation for question {i}",
                "steps": [f"Step 1 for question {i}", f"Step 2 for question {i}"],
            },
            "hint": f"Hint for question {i}",
            "metadata": {
                "created_by": "admin",
                "created_at": datetime(2024, 12, 20, 10, 0, 0),
                "updated_at": datetime(2024, 12, 20, 12, 0, 0),
                "time_estimate": 5,
            },
        }
        for i in range(10)
    ]
    engine.fetch_from_db.return_value = collection
    return engine


@pytest.fixture
def recommendation_engine(sample_config, mock_performance_engine, mock_database_engine):
    return RecommendationEngine(
        performance_engine=mock_performance_engine,
        database_engine=mock_database_engine,
        config=sample_config,
    )
