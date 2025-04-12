from datetime import datetime

import factory
from bson import ObjectId
from factory import Factory, Faker, Sequence, SubFactory
from factory.django import DjangoModelFactory

from course_ware.models import (
    AcademicClass,
    CoreElement,
    Course,
    EdxUser,
    ExaminationLevel,
    SubTopic,
    Topic,
    UserQuestionAttempts,
    UserQuestionSet,
)
from data_types.course_ware_schema import QuestionMetadata
from repository.data_types import Choice, Metadata, Question, Solution


class UserFactory(DjangoModelFactory):
    class Meta:
        model = EdxUser

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


class ExaminationLevelFactory(DjangoModelFactory):
    class Meta:
        model = ExaminationLevel

    name = Faker("word")


class CoreElementFactory(DjangoModelFactory):
    class Meta:
        model = CoreElement

    name = Faker("word")


class TopicFactory(DjangoModelFactory):
    class Meta:
        model = Topic

    name = Faker("word")
    course = SubFactory(CourseFactory)
    academic_class = SubFactory(AcademicClassFactory)
    examination_level = SubFactory(ExaminationLevelFactory)
    core_element = SubFactory(CoreElementFactory)
    block_id = factory.Sequence(lambda n: f"chapter{n}")
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class SubTopicFactory(DjangoModelFactory):
    class Meta:
        model = SubTopic

    name = Faker("word")
    topic = SubFactory(TopicFactory)
    block_id = factory.Sequence(lambda n: f"chapter{n}")


class QuestionMetadataFactory(Factory):
    class Meta:
        model = QuestionMetadata

    question_id = factory.LazyFunction(lambda: str(ObjectId()))
    attempt_number = Faker("random_int", min=1, max=3)
    is_correct = Faker("boolean")
    topic = Faker("word")
    difficulty = Faker("random_element", elements=["easy", "medium", "hard"])


def generate_question_metadata():
    """
    Generate a dictionary where keys and values' 'id' fields match.
    """

    def create_question():
        question = QuestionMetadataFactory()
        question_id = question.question_id
        return question_id, vars(question)

    return {
        "v1.0.0": dict(create_question() for _ in range(2)),
        "v2.0.0": dict(create_question() for _ in range(1)),
    }


class UserQuestionAttemptsFactory(DjangoModelFactory):
    class Meta:
        model = UserQuestionAttempts

    user = SubFactory(UserFactory)
    topic = SubFactory(SubTopicFactory)
    question_metadata = factory.LazyFunction(generate_question_metadata)


class UserQuestionSetFactory(DjangoModelFactory):
    class Meta:
        model = UserQuestionSet

    user = SubFactory(UserFactory)
    topic = SubFactory(SubTopicFactory)
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

    _id = factory.LazyFunction(lambda: str(ObjectId()))
    question_id = factory.LazyFunction(lambda: str(ObjectId()))
    text = factory.Faker("sentence")
    sub_topic = factory.Faker("word")
    topic = factory.Faker("word")
    academic_class = factory.Faker("word")
    examination_level = factory.Faker("word")
    difficulty = factory.Faker("word")
    tags = factory.List([factory.Faker("word") for _ in range(3)])
    choices = factory.List([ChoiceFactory() for _ in range(4)])
    solution = factory.SubFactory(SolutionFactory)
    hint = factory.Faker("sentence")
    metadata = factory.SubFactory(MetadataFactory)
