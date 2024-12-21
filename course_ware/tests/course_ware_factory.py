from factory import Dict, Factory, Faker, Sequence, SubFactory
from factory.django import DjangoModelFactory

from course_ware.models import (
    AcademicClass,
    Category,
    Course,
    Topic,
    User,
    UserQuestionAttempts,
    UserQuestionSet,
)
from data_types.course_ware_schema import QuestionMetadata


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = Faker("user_name")
    email = Faker("email")
    id = Sequence(lambda n: n + 1)


class AcademicClassFactory(DjangoModelFactory):
    class Meta:
        model = AcademicClass

    name = Faker("name")


class CourseFactory(DjangoModelFactory):
    class Meta:
        model = Course

    name = Faker("name")
    course_key = Faker("uuid4")
    course_structure = Faker("json")


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    course = SubFactory(CourseFactory)
    academic_class = SubFactory(AcademicClassFactory)


class TopicFactory(DjangoModelFactory):
    class Meta:
        model = Topic

    name = Faker("word")
    description = Faker("text")
    is_completed = Faker("boolean")
    category = SubFactory(CategoryFactory)


class QuestionMetadataFactory(Factory):
    class Meta:
        model = QuestionMetadata

    question_id = Faker("uuid4")
    attempt_number = Faker("random_int", min=1, max=10)
    is_correct = Faker("boolean")
    topic = Faker("word")
    difficulty = Faker("random_element", elements=["easy", "medium", "hard"])


class UserQuestionAttemptsFactory(DjangoModelFactory):
    class Meta:
        model = UserQuestionAttempts

    user = SubFactory(UserFactory)
    topic = SubFactory(TopicFactory)
    question_metadata = Dict(
        {
            "v1.0.0": {
                "question1": QuestionMetadataFactory().__dict__,
                "question2": QuestionMetadataFactory().__dict__,
            },
            "v2.0.0": {"question1": QuestionMetadataFactory().__dict__},
        }
    )


class UserQuestionSetFactory(DjangoModelFactory):
    class Meta:
        model = UserQuestionSet

    user = SubFactory(UserFactory)
    topic = SubFactory(TopicFactory)
    question_set_ids = "[]"
