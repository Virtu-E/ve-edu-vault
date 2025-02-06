from unittest.mock import Mock

import pytest

from ai_core.contextual_analyzer.context_builder import QuestionContextBuilder
from course_ware.tests.course_ware_factory import QuestionFactory, QuestionMetadataFactory
from data_types.ai_core import QuestionAIContext
from exceptions import InvalidQuestionConfiguration
from repository.shared import QuestionRepository


class TestQuestionContextBuilder:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up the test environment for QuestionContextBuilder."""
        self.question_repository = Mock(spec=QuestionRepository)
        self.question_context_builder = QuestionContextBuilder(self.question_repository)

        self.q1_id = "679145a22c18aa8716206e9f"
        self.q2_id = "679145a22c18aa8716206ea5"

        self.sample_questions = [
            QuestionFactory(
                _id=self.q1_id,
                question_id=self.q1_id,
                difficulty="easy",
                tags=["math", "algebra"],
            ),
            QuestionFactory(
                _id=self.q2_id,
                question_id=self.q2_id,
                difficulty="hard",
                tags=["physics", "mechanics"],
            ),
        ]

        self.sample_metadata = {
            self.q1_id: QuestionMetadataFactory(
                is_correct=True,
                attempt_number=1,
                difficulty="easy",
                question_id=self.q1_id,
            ),
            self.q2_id: QuestionMetadataFactory(
                is_correct=False,
                attempt_number=2,
                difficulty="hard",
                question_id=self.q2_id,
            ),
        }

    def test_build_question_context_successful(self):
        """Test successful building of question context."""
        question_ids = [self.q1_id, self.q2_id]
        self.question_repository.get_questions_by_ids.return_value = self.sample_questions

        result = self.question_context_builder.build_question_context(question_ids, self.sample_metadata)

        assert len(result) == 2
        assert all(isinstance(context, QuestionAIContext) for context in result)

        # Verify first question context
        assert result[0].id == self.q1_id
        assert result[0].difficulty == "easy"
        assert result[0].tags == ["math", "algebra"]
        assert result[0].attempts.success is True
        assert result[0].attempts.attemptNumber == 1
        assert result[0].attempts.timeSpent == 90

        # Verify second question context
        assert result[1].id == self.q2_id
        assert result[1].difficulty == "hard"
        assert result[1].tags == ["physics", "mechanics"]
        assert result[1].attempts.success is False
        assert result[1].attempts.attemptNumber == 2
        assert result[1].attempts.timeSpent == 90

    def test_build_question_context_missing_metadata(self):
        """Test building question context with missing metadata."""
        question_ids = [self.q1_id, self.q2_id]
        self.question_repository.get_questions_by_ids.return_value = self.sample_questions
        metadata = {
            self.q1_id: QuestionMetadataFactory(
                is_correct=True,
                attempt_number=1,
                difficulty="easy",
                question_id=self.q1_id,
            )
        }  # Missing second question metadata

        with pytest.raises(InvalidQuestionConfiguration) as exc_info:
            self.question_context_builder.build_question_context(question_ids, metadata)

        assert str(exc_info.value) == f"Invalid parameter: 'Question {self.q2_id} not found in attempt data'"

    def test_build_question_context_empty_input(self):
        """Test building question context with empty input."""
        question_ids = []
        metadata = {}
        self.question_repository.get_questions_by_ids.return_value = []

        result = self.question_context_builder.build_question_context(question_ids, metadata)

        assert result == []
        self.question_repository.get_questions_by_ids.assert_called_once_with([])

    def test_build_question_context_with_different_attempt_data(self):
        """Test building question context with different attempt data."""
        question = QuestionFactory(_id=self.q1_id, question_id=self.q1_id, difficulty="easy", tags=["math"])
        metadata = {
            self.q1_id: QuestionMetadataFactory(
                is_correct=False,
                attempt_number=3,
                difficulty="easy",
                question_id=self.q1_id,
            )
        }
        self.question_repository.get_questions_by_ids.return_value = [question]

        result = self.question_context_builder.build_question_context([self.q1_id], metadata)

        assert len(result) == 1
        assert result[0].id == self.q1_id
        assert result[0].attempts.success is False
        assert result[0].attempts.attemptNumber == 3
        assert result[0].attempts.timeSpent == 90

    def test_build_question_context_with_invalid_question_id(self):
        """Test building question context with an invalid question ID."""
        invalid_id = "679145a22c18aa8716206e99"
        self.question_repository.get_questions_by_ids.return_value = []
        metadata = {
            invalid_id: QuestionMetadataFactory(
                is_correct=True,
                attempt_number=1,
                difficulty="easy",
                question_id=invalid_id,
            )
        }

        result = self.question_context_builder.build_question_context([invalid_id], metadata)

        assert len(result) == 0
        self.question_repository.get_questions_by_ids.assert_called_once_with([invalid_id])

    def test_build_question_context_with_none_metadata(self):
        """Test building question context with None as metadata."""
        question_ids = [self.q1_id]
        self.question_repository.get_questions_by_ids.return_value = [self.sample_questions[0]]
        metadata = {self.q1_id: None}  # None metadata

        with pytest.raises(InvalidQuestionConfiguration) as exc_info:
            self.question_context_builder.build_question_context(question_ids, metadata)

        assert str(exc_info.value) == f"Invalid parameter: 'Question {self.q1_id} not found in attempt data'"

    def test_build_question_context_with_none_question_ids(self):
        """Test building question context with None as question IDs."""
        question_ids = None

        with pytest.raises(TypeError):
            self.question_context_builder.build_question_context(question_ids, self.sample_metadata)

    def test_build_question_context_with_none_metadata_dict(self):
        """Test building question context with None as metadata dictionary."""
        question_ids = [self.q1_id]
        metadata = None

        with pytest.raises(TypeError):
            self.question_context_builder.build_question_context(question_ids, metadata)

    def test_build_question_context_with_invalid_metadata_structure(self):
        """Test building question context with invalid metadata structure."""
        question_ids = [self.q1_id]
        self.question_repository.get_questions_by_ids.return_value = [self.sample_questions[0]]
        metadata = {
            self.q1_id: {
                # Missing required fields
                "some_other_field": "value"
            }
        }

        with pytest.raises(AttributeError):
            self.question_context_builder.build_question_context(question_ids, metadata)

    def test_build_question_context_with_duplicate_question_ids(self):
        """Test building question context with duplicate question IDs."""
        question_ids = [self.q1_id, self.q1_id]  # Duplicate IDs
        self.question_repository.get_questions_by_ids.return_value = [self.sample_questions[0]]

        result = self.question_context_builder.build_question_context(question_ids, self.sample_metadata)

        assert len(result) == 1  # Should only return one context even with duplicate IDs
        assert result[0].id == self.q1_id

    def test_build_question_context_with_mismatched_metadata_question_id(self):
        """Test building question context with mismatched metadata question ID."""
        question_ids = [self.q1_id]
        self.question_repository.get_questions_by_ids.return_value = [self.sample_questions[0]]
        metadata = {
            self.q1_id: QuestionMetadataFactory(
                is_correct=True,
                attempt_number=1,
                difficulty="easy",
                question_id=self.q2_id,  # Mismatched question_id
            )
        }

        result = self.question_context_builder.build_question_context(question_ids, metadata)

        assert len(result) == 1
        assert result[0].id == self.q1_id
        assert result[0].attempts.success is True

    def test_build_question_context_when_repository_returns_none(self):
        """Test building question context when the repository returns None."""
        question_ids = [self.q1_id]
        self.question_repository.get_questions_by_ids.return_value = None

        with pytest.raises(TypeError):
            self.question_context_builder.build_question_context(question_ids, self.sample_metadata)

    def test_build_question_context_with_empty_tags(self):
        """Test building question context with empty tags for a question."""
        question = QuestionFactory(
            _id=self.q1_id,
            question_id=self.q1_id,
            difficulty="easy",
            tags=[],  # Empty tags
        )
        self.question_repository.get_questions_by_ids.return_value = [question]

        result = self.question_context_builder.build_question_context([self.q1_id], self.sample_metadata)

        assert len(result) == 1
        assert result[0].tags == []
