import pytest

from course_ware.course_sync import CourseSync
from course_ware.tests.course_ware_factory import (
    AcademicClassFactory,
    CategoryFactory,
    CourseFactory,
    TopicFactory,
)


@pytest.fixture
def course():
    return CourseFactory()


@pytest.fixture
def academic_class():
    return AcademicClassFactory()


@pytest.fixture
def category(course):
    return CategoryFactory(course=course)


@pytest.fixture
def topic(category):
    return TopicFactory(category=category)


@pytest.fixture
def course_sync(course, academic_class):
    return CourseSync(course, academic_class)
