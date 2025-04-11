import pytest

from course_ware.tests.course_ware_factory import (
    CourseFactory,
    SubTopicFactory,
    TopicFactory,
)
from data_types.course_ware_models import EdxUserData


@pytest.fixture
def edx_user_data():
    return EdxUserData(
        id=1,
        username="test_user",
        email="test@example.com",
        course_key="test-course-key",
    )


@pytest.fixture
def course():
    return CourseFactory(course_key="test-course-key")


@pytest.fixture
def topic(course):
    return TopicFactory(course=course)


@pytest.fixture
def sub_topics(category):
    return [SubTopicFactory(category=category), SubTopicFactory(category=category)]
