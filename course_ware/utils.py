import logging

from django.db import transaction

from data_types.course_ware_models import EdxUserData
from exceptions import DatabaseUpdateError
from .models import (
    Category,
    User,
    UserCategoryProgress,
    UserQuestionAttempts,
    UserQuestionSet,
)

log = logging.getLogger(__name__)


# TODO : attach to course enrollment signal
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
            log.info(f"User {edx_user_data.username} created")

            # 2. Get all categories for the user's courses
            user_categories = Category.objects.filter(
                course__course_key=edx_user_data.course_key
            )

            # 3. Initialize progress tracking and question sets for each category
            for category in user_categories:
                # Create category progress
                UserCategoryProgress.objects.create(user=user, category=category)

                log.info(
                    f"Created Course Category {category.name} for user {edx_user_data.username}"
                )

                # Initialize data for each topic in the category
                for topic in category.topics.all():
                    # Create empty question set
                    UserQuestionSet.objects.create(
                        user=user,
                        topic=topic,
                        question_list_ids=[],  # TODO : set default for each known categories
                    )

                    log.info(
                        f"Question set created for topic: {topic.name}, user: {edx_user_data.username}"
                    )

                    # Initialize question attempts tracking
                    UserQuestionAttempts.objects.create(
                        user=user,
                        topic=topic,
                        question_metadata={"v1.0.0": {}},
                    )

                    log.info(
                        f"Question attempt created for topic: {topic.name}, user: {edx_user_data.username}"
                    )

            return user

    except Exception as e:
        log.error(
            f"Failed to initialize edu vault user {edx_user_data.username}, with default database values : {e}"
        )
        raise DatabaseUpdateError(
            f"Failed to initialize edu vault user {edx_user_data.username}, with default database values : {e}"
        )


def academic_class_from_course_id(course_id: str) -> str | None:
    """
    Function to get Academic class from course id
    """
    parts = course_id.split(":")

    course_parts = parts[-1].split("+")

    program = course_parts[1]
    number = course_parts[2]

    first_digit = int(number[0])

    if program == "MSCE":
        if first_digit == 3 or first_digit == 4:
            return "Form 4"
    elif program == "JCE":
        if first_digit == 1:
            return "Form 1"
        elif first_digit == 2:
            return "Form 2"

    return None


def get_examination_level_from_course_id(course_id: str) -> str:
    """
    Function to get examination level from course id
    """
    parts = course_id.split(":")

    course_parts = parts[-1].split("+")

    return course_parts[1]
