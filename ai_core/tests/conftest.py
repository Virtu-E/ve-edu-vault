import pytest

from course_ware.tests.course_ware_factory import UserFactory, TopicFactory


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Automatically enable database access for all tests."""
    pass


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def topic():
    return TopicFactory()
