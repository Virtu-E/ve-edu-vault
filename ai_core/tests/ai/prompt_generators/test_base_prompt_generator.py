import pytest

from ai_core.ai.prompt_generators.base_prompt_generator import BaseQuestionPromptGenerator
from ai_core.learning_mode_rules import BaseLearningModeRule, LearningModeType, NormalRule
from ai_core.tests.ai_core_factories import ModeDataFactory
from data_types.ai_core import LearningHistory, QuestionPromptGeneratorConfig
from repository.ai_core.prompt_engine import PromptEngineRepositoryInterface


class MockPromptEngineRepository(PromptEngineRepositoryInterface):
    def get_question_bank(self, question_ids):
        return "Mock Question Bank"


@pytest.fixture
def learning_history(user, topic):
    return LearningHistory(
        userId=user.id,
        block_id=topic.block_id,
        modeHistory={"normal": [ModeDataFactory()]},
    )


@pytest.fixture
def config():
    return QuestionPromptGeneratorConfig(
        course_name="Mathematics",
        topic_name="Algebra",
        difficulty="medium",
        academic_level="High School",
        syllabus="Basic Algebra",
        category="Math",
    )


@pytest.fixture
def repository():
    return MockPromptEngineRepository()


class TestBaseQuestionPromptGenerator:
    def test_init_with_valid_data(self, learning_history, repository, config):
        rule = NormalRule()
        generator = BaseQuestionPromptGenerator(
            rule=rule,
            learning_history=learning_history,
            repository=repository,
            question_ids=["1", "2"],
            config=config,
            failed_difficulties=["easy", "medium"],
        )
        assert generator.rule == rule
        assert generator.learning_history == learning_history
        assert generator.repository == repository

    def test_validate_prerequisite_with_missing_prerequisite(self, learning_history, repository, config):
        class TestRule(BaseLearningModeRule):
            prerequisite = LearningModeType.REINFORCEMENT

        with pytest.raises(ValueError) as exc_info:
            BaseQuestionPromptGenerator(
                rule=TestRule(),
                learning_history=learning_history,
                repository=repository,
                question_ids=["1", "2"],
                config=config,
                failed_difficulties=["easy"],
            )
        assert "Learning history does not contain the required prerequisite" in str(exc_info.value)

    def test_generate_question_prompt(self, learning_history, repository, config):
        rule = NormalRule()
        generator = BaseQuestionPromptGenerator(
            rule=rule,
            learning_history=learning_history,
            repository=repository,
            question_ids=["1", "2"],
            config=config,
            failed_difficulties=["easy", "medium"],
        )
        prompt = generator.generate_question_prompt()

        assert isinstance(prompt, str)
        assert "Current Course: Mathematics" in prompt
        assert "Current Topic: Algebra" in prompt
        assert "Mock Question Bank" in prompt

    def test_get_failed_tags(self, learning_history, repository, config):
        rule = NormalRule()
        generator = BaseQuestionPromptGenerator(
            rule=rule,
            learning_history=learning_history,
            repository=repository,
            question_ids=["1", "2"],
            config=config,
            failed_difficulties=["easy"],
        )
        failed_tags = generator.learning_history.get_failed_tags("normal")
        assert isinstance(failed_tags, dict)
        assert "easy" in failed_tags
        assert isinstance(failed_tags["easy"], list)
