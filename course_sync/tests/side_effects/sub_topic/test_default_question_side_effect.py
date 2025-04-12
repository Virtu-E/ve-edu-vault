from unittest.mock import MagicMock, patch

import pytest

from course_ware.models import DefaultQuestionSet, SubTopic
from course_ware.tests.course_ware_factory import (
    DefaultQuestionSetFactory,
    SubTopicFactory,
)


class TestDefaultQuestionSetAssignerMixin:

    def test_sync_question_set_creates_new_record(
        self, mixin_instance, sample_questions
    ):
        """Test that sync_question_set creates a new DefaultQuestionSet when one doesn't exist"""
        subtopic = SubTopicFactory()

        mixin_instance.sync_question_set(sample_questions, subtopic)

        question_set = DefaultQuestionSet.objects.get(sub_topic=subtopic)
        assert question_set is not None
        assert question_set.question_list_ids == sample_questions

    def test_sync_question_set_updates_existing_record(
        self, mixin_instance, sample_questions
    ):
        """Test that sync_question_set updates an existing DefaultQuestionSet"""
        subtopic = SubTopicFactory()
        old_questions = [{"id": "old1"}]
        DefaultQuestionSetFactory(sub_topic=subtopic, question_list_ids=old_questions)

        mixin_instance.sync_question_set(sample_questions, subtopic)

        question_set = DefaultQuestionSet.objects.get(sub_topic=subtopic)
        assert question_set.question_list_ids == sample_questions

    def test_sync_question_set_handles_subtopic_does_not_exist(
        self, mixin_instance, sample_questions
    ):
        """Test that sync_question_set raises appropriate exception when subtopic doesn't exist"""
        non_existent_subtopic = MagicMock(spec=SubTopic)
        non_existent_subtopic.id = 999
        non_existent_subtopic.name = "Non-existent"

        with patch.object(
            DefaultQuestionSet.objects, "update_or_create"
        ) as mock_update:
            mock_update.side_effect = SubTopic.DoesNotExist()

            with pytest.raises(SubTopic.DoesNotExist):
                mixin_instance.sync_question_set(
                    sample_questions, non_existent_subtopic
                )


def test_sync_question_set_with_empty_questions(mixin_instance, empty_questions):
    """Test sync_question_set with an empty questions list"""

    subtopic = SubTopicFactory()

    mixin_instance.sync_question_set(empty_questions, subtopic)

    question_set = DefaultQuestionSet.objects.get(sub_topic=subtopic)
    assert question_set.question_list_ids == empty_questions


def test_sync_question_set_with_different_question_format(
    mixin_instance, different_format_questions
):
    """Test sync_question_set with questions in a different format"""
    subtopic = SubTopicFactory()

    mixin_instance.sync_question_set(different_format_questions, subtopic)

    question_set = DefaultQuestionSet.objects.get(sub_topic=subtopic)
    assert question_set.question_list_ids == different_format_questions
