import pytest

from course_ware.models import (
    User,
    UserCategoryProgress,
    UserQuestionAttempts,
    UserQuestionSet,
)
from course_ware.utils import initialize_edu_vault_user
from exceptions import DatabaseUpdateError


def test_initialize_edu_vault_user_success(edx_user_data, course, category, topics):
    """Test successful initialization of edu vault user"""
    # Execute
    user = initialize_edu_vault_user(edx_user_data)

    # Verify user creation
    assert User.objects.filter(id=edx_user_data.id).exists()
    assert user.username == edx_user_data.username
    assert user.email == edx_user_data.email
    assert user.active is True

    # Verify category progress creation
    category_progress = UserCategoryProgress.objects.filter(user=user)
    assert category_progress.count() == 1
    assert category_progress.first().category == category

    # Verify question sets and attempts for each topic
    for topic in topics:
        # Check question set
        question_set = UserQuestionSet.objects.get(user=user, topic=topic)
        assert question_set.question_set_ids == []

        # Check question attempts
        question_attempts = UserQuestionAttempts.objects.get(user=user, topic=topic)
        assert question_attempts.question_metadata == {"v1.0.0": {}}


def test_initialize_edu_vault_user_no_categories(edx_user_data, course):
    """Test initialization when no categories exist for the course"""
    user = initialize_edu_vault_user(edx_user_data)

    assert User.objects.filter(id=edx_user_data.id).exists()
    assert UserCategoryProgress.objects.filter(user=user).count() == 0
    assert UserQuestionSet.objects.filter(user=user).count() == 0
    assert UserQuestionAttempts.objects.filter(user=user).count() == 0


def test_initialize_edu_vault_user_duplicate_user(edx_user_data, course, category):
    """Test handling of duplicate user creation"""
    # Create user first time
    initialize_edu_vault_user(edx_user_data)

    # Attempt to create same user again
    with pytest.raises(DatabaseUpdateError):
        initialize_edu_vault_user(edx_user_data)


def test_initialize_edu_vault_user_transaction_rollback(
    edx_user_data, course, category, topics, mocker
):
    """Test transaction rollback on failure"""
    # Mock UserQuestionSet.objects.create to raise an exception
    mocker.patch(
        "models.UserQuestionSet.objects.create", side_effect=Exception("Test error")
    )

    with pytest.raises(DatabaseUpdateError):
        initialize_edu_vault_user(edx_user_data)

    # Verify nothing was created due to transaction rollback
    assert not User.objects.filter(id=edx_user_data.id).exists()
    assert not UserCategoryProgress.objects.filter(user__id=edx_user_data.id).exists()
    assert not UserQuestionAttempts.objects.filter(user__id=edx_user_data.id).exists()
