from django.db import transaction

from data_types.course_ware_models import EdxUserData

from .models import (
    Category,
    User,
    UserCategoryProgress,
    UserQuestionAttempts,
    UserQuestionSet,
)


def initialize_edu_vault_user(edx_user_data: EdxUserData):
    """
    Initializes all the necessary database tables for a new edx user with edu vault.
    This function creates all required records and their relationships in a single transaction.

    Args:
        edx_user_data (EdxUserData): User data from edX platform

    Returns:
        User: The created User instance

    Raises:
        Exception: If any part of the initialization fails
    """
    try:
        with transaction.atomic():
            # 1. Create the user
            user = User.objects.create(
                id=edx_user_data.id,
                username=edx_user_data.username,
                email=edx_user_data.email,
                active=True,
            )

            # 2. Get all categories for the user's courses
            user_categories = Category.objects.filter(
                course__course_key__in=edx_user_data.enrolled_courses
            )

            # 3. Initialize progress tracking and question sets for each category
            for category in user_categories:
                # Create category progress
                UserCategoryProgress.objects.create(
                    user=user, category=category, is_completed=False
                )

                # Initialize data for each topic in the category
                for topic in category.topics.all():
                    # Create empty question set
                    UserQuestionSet.objects.create(
                        user=user,
                        topic=topic,
                        question_set_ids=[],  # Empty list to be populated later
                    )

                    # Initialize question attempts tracking
                    UserQuestionAttempts.objects.create(
                        user=user,
                        topic=topic,
                        question_metadata={
                            "v1.0.0": {
                                "attempts": [],
                                "total_attempts": 0,
                                "successful_attempts": 0,
                                "last_attempt_timestamp": None,
                            }
                        },
                    )

            return user

    except Exception as e:
        # Log the error appropriately
        raise Exception(f"Failed to initialize edu vault user: {str(e)}")
