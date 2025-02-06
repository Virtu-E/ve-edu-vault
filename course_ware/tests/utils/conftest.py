import pytest

from course_ware.tests.course_ware_factory import CategoryFactory, CourseFactory, TopicFactory
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
def category(course):
    return CategoryFactory(course=course)


@pytest.fixture
def topics(category):
    return [TopicFactory(category=category), TopicFactory(category=category)]
