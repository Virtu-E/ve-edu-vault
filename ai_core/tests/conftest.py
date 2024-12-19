import pytest

from ai_core.tests.performance_engine.performance_engine_factory import UserFactory


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Automatically enable database access for all tests."""
    pass


@pytest.fixture
def user():
    return UserFactory()
