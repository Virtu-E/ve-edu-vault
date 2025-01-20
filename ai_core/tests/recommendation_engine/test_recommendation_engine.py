import json
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from asgiref.sync import sync_to_async

from course_ware.models import UserQuestionSet
from course_ware.tests.course_ware_factory import (
    UserQuestionAttemptsFactory,
    UserQuestionSetFactory,
)
from data_types.ai_core import RecommendationQuestionMetadata
from data_types.questions import Choice, Metadata, Question, Solution
from exceptions import (
    DatabaseUpdateError,
    InsufficientQuestionsError,
    QuestionFetchError,
)


@pytest.mark.asyncio
class TestRecommendationEngine:
    async def test_init(self, recommendation_engine, sample_config):
        """Test initialization of RecommendationEngine"""
        assert recommendation_engine.database_name == sample_config.database_name
        assert recommendation_engine.collection_name == sample_config.collection_name
        assert recommendation_engine.user_id == sample_config.user_id
        assert recommendation_engine.topic_id == sample_config.topic_id

    async def test_get_questions_list_from_database(self, recommendation_engine):
        """Test fetching questions from database"""
        questions = await recommendation_engine._get_questions_list_from_database(
            "easy"
        )
        assert len(questions) == 10
        assert all(isinstance(q, Question) for q in questions)

    async def test_get_questions_list_database_error(
        self, recommendation_engine, mock_database_engine
    ):
        """Test handling database errors when fetching questions"""
        mock_database_engine.fetch_from_db.side_effect = Exception("Database error")

        with pytest.raises(QuestionFetchError):
            await recommendation_engine._get_questions_list_from_database("easy")

    @pytest.mark.skip(reason="not implemented")
    async def test_set_users_recommended_questions_success(
        self, recommendation_engine, mock_performance_engine
    ):
        """Test successful setting of recommended questions"""
        # Create test data
        await sync_to_async(UserQuestionSetFactory)(
            user_id=recommendation_engine.user_id,
            topic_id=recommendation_engine.topic_id,
        )
        await sync_to_async(UserQuestionAttemptsFactory)(
            user_id=recommendation_engine.user_id,
            topic_id=recommendation_engine.topic_id,
            question_metadata={"v1.0.0": {}},
        )

        # Execute test
        await recommendation_engine.set_users_recommended_questions()

        # Verify results
        updated_question_set = await UserQuestionSet.objects.aget(
            user_id=recommendation_engine.user_id,
            topic_id=recommendation_engine.topic_id,
        )
        question_ids = json.loads(updated_question_set.question_set_ids)
        assert len(question_ids) > 0
        assert all(isinstance(q["id"], str) for q in question_ids)

    @pytest.mark.skip(reason="not implemented")
    async def test_insufficient_questions(
        self, recommendation_engine, mock_database_engine
    ):
        """Test handling insufficient questions scenario"""
        # Mock database to return fewer questions than the minimum threshold
        collection = AsyncMock()
        collection.find.return_value = [
            {
                "_id": f"question_{i}",
                "question_id": f"Q{i:04}",
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
                "solution": {"explanation": f"Explanation for question {i}"},
                "hint": f"Hint for question {i}",
                "metadata": {
                    "created_by": "admin",
                    "created_at": datetime(2024, 12, 20, 10, 0, 0),
                    "updated_at": datetime(2024, 12, 20, 12, 0, 0),
                },
            }
            for i in range(recommendation_engine.MINIMUM_QUESTIONS_THRESHOLD - 1)
        ]
        mock_database_engine.fetch_from_db.return_value = collection

        with pytest.raises(InsufficientQuestionsError):
            await recommendation_engine.set_users_recommended_questions()

    async def test_build_query(self, recommendation_engine):
        """Test database query building"""
        query = recommendation_engine._build_query("medium")
        assert query.difficulty == "medium"
        assert query.category == recommendation_engine.metadata.category
        assert query.topic == recommendation_engine.metadata.topic

    async def test_exclude_current_users_questions(self, recommendation_engine):
        """Test filtering out existing questions"""
        current_ids = {"question_1", "question_2"}
        from datetime import datetime

        questions = [
            Question(
                _id="question_1",
                question_id="question_1",
                text="Test question 1",
                topic="Mathematics",
                category="Algebra",
                academic_class="10th Grade",
                examination_level="Intermediate",
                difficulty="easy",
                tags=["math", "algebra", "practice"],
                choices=[
                    Choice(text="Choice 1", is_correct=True),
                    Choice(text="Choice 2", is_correct=False),
                    Choice(text="Choice 3", is_correct=False),
                    Choice(text="Choice 4", is_correct=False),
                ],
                solution=Solution(
                    explanation="Explanation for question 1",
                    steps=["Step 1: Analyze the equation", "Step 2: Solve for x"],
                ),
                hint="Hint for question 1",
                metadata=Metadata(
                    created_by="admin",
                    created_at=datetime(2024, 12, 20, 10, 0, 0),
                    updated_at=datetime(2024, 12, 20, 12, 0, 0),
                    time_estimate=5,
                ),
            ),
            Question(
                _id="question_2",
                question_id="question_2",
                text="Test question 2",
                topic="Physics",
                category="Mechanics",
                academic_class="11th Grade",
                examination_level="Advanced",
                difficulty="medium",
                tags=["physics", "mechanics", "practice"],
                choices=[
                    Choice(text="Option A", is_correct=False),
                    Choice(text="Option B", is_correct=True),
                    Choice(text="Option C", is_correct=False),
                    Choice(text="Option D", is_correct=False),
                ],
                solution=Solution(
                    explanation="Explanation for question 2",
                    steps=["Step 1: Analyze the forces", "Step 2: Apply Newton's laws"],
                ),
                hint="Hint for question 2",
                metadata=Metadata(
                    created_by="teacher",
                    created_at=datetime(2024, 12, 19, 14, 0, 0),
                    updated_at=datetime(2024, 12, 20, 9, 30, 0),
                    time_estimate=10,
                ),
            ),
            Question(
                _id="question_3",
                question_id="question_3",
                text="Test question 3",
                topic="Chemistry",
                category="Organic Chemistry",
                academic_class="12th Grade",
                examination_level="Beginner",
                difficulty="hard",
                tags=["chemistry", "organic", "study"],
                choices=[
                    Choice(text="Answer 1", is_correct=False),
                    Choice(text="Answer 2", is_correct=False),
                    Choice(text="Answer 3", is_correct=True),
                    Choice(text="Answer 4", is_correct=False),
                ],
                solution=Solution(
                    explanation="Explanation for question 3",
                    steps=[
                        "Step 1: Identify functional groups",
                        "Step 2: Predict reaction mechanism",
                    ],
                ),
                hint="Hint for question 3",
                metadata=Metadata(
                    created_by="admin",
                    created_at=datetime(2024, 12, 18, 16, 0, 0),
                    updated_at=datetime(2024, 12, 20, 8, 45, 0),
                    time_estimate=15,
                ),
            ),
            Question(
                _id="question_4",
                question_id="question_4",
                text="Test question 4",
                topic="Biology",
                category="Genetics",
                academic_class="12th Grade",
                examination_level="Intermediate",
                difficulty="easy",
                tags=["biology", "genetics", "revision"],
                choices=[
                    Choice(text="Option 1", is_correct=False),
                    Choice(text="Option 2", is_correct=False),
                    Choice(text="Option 3", is_correct=True),
                    Choice(text="Option 4", is_correct=False),
                ],
                solution=Solution(
                    explanation="Explanation for question 4",
                    steps=[
                        "Step 1: Understand Mendelian ratios",
                        "Step 2: Apply Punnett square",
                    ],
                ),
                hint="Hint for question 4",
                metadata=Metadata(
                    created_by="teacher",
                    created_at=datetime(2024, 12, 17, 11, 0, 0),
                    updated_at=datetime(2024, 12, 19, 13, 15, 0),
                    time_estimate=8,
                ),
            ),
        ]
        filtered = recommendation_engine._exclude_current_users_questions(
            questions, current_ids
        )
        assert len(filtered) == 2
        assert all(q.question_id not in current_ids for q in filtered)

    async def test_database_update_error(
        self, recommendation_engine, mock_database_engine
    ):
        """Test handling database update errors"""
        mock_database_engine.fetch_from_db.side_effect = Exception("Update failed")

        with pytest.raises(DatabaseUpdateError):
            await recommendation_engine.set_users_recommended_questions()


def test_question_metadata():
    """Test QuestionMetadata dataclass"""
    metadata = RecommendationQuestionMetadata(
        category="math",
        topic="algebra",
        examination_level="high_school",
        academic_class="10th",
        difficulty="medium",
    )
    assert metadata.category == "math"
    assert metadata.topic == "algebra"
    assert metadata.difficulty == "medium"
