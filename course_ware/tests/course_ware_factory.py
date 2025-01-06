from datetime import datetime

import factory
from bson import ObjectId
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
from data_types.questions import Choice, Metadata, Question, Solution


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
    course_outline = {
        "chapter1": {
            "type": "chapter",
            "display_name": "Chapter 1",
            "description": "First chapter",
            "children": ["sequential1"],
        },
        "sequential1": {
            "type": "sequential",
            "display_name": "Sequential 1",
            "description": "First sequential",
            "children": [],
        },
    }


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    course = SubFactory(CourseFactory)
    academic_class = SubFactory(AcademicClassFactory)
    block_id = factory.Sequence(lambda n: f"chapter{n}")
    description = factory.Sequence(lambda n: f"Description {n}")


class TopicFactory(DjangoModelFactory):
    class Meta:
        model = Topic

    name = Faker("word")
    is_completed = Faker("boolean")
    category = SubFactory(CategoryFactory)
    block_id = factory.Sequence(lambda n: f"chapter{n}")
    description = factory.Sequence(lambda n: f"Description {n}")


class QuestionMetadataFactory(Factory):
    class Meta:
        model = QuestionMetadata

    question_id = Faker("uuid4")
    attempt_number = Faker("random_int", min=1, max=3)
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
    question_list_ids = []


class ChoiceFactory(factory.Factory):
    class Meta:
        model = Choice

    text = factory.Faker("sentence")
    is_correct = factory.Faker("boolean")


class SolutionFactory(factory.Factory):
    class Meta:
        model = Solution

    explanation = factory.Faker("sentence")
    steps = factory.List([factory.Faker("sentence") for _ in range(3)])


class MetadataFactory(factory.Factory):
    class Meta:
        model = Metadata

    created_by = factory.Faker("name")
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    time_estimate = factory.Faker("random_int", min=1, max=60)


class QuestionFactory(factory.Factory):
    class Meta:
        model = Question

    id = factory.LazyFunction(lambda: str(ObjectId()))
    question_id = factory.Faker("uuid4")
    text = factory.Faker("sentence")
    topic = factory.Faker("word")
    category = factory.Faker("word")
    academic_class = factory.Faker("word")
    examination_level = factory.Faker("word")
    difficulty = factory.Faker("word")
    tags = factory.List([factory.Faker("word") for _ in range(3)])
    choices = factory.List([ChoiceFactory() for _ in range(4)])
    solution = factory.SubFactory(SolutionFactory)
    hint = factory.Faker("sentence")
    metadata = factory.SubFactory(MetadataFactory)
