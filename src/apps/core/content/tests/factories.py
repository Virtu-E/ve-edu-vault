from datetime import datetime

import factory.fuzzy
from factory.django import DjangoModelFactory

from src.apps.core.courses.tests.factories import (
    AcademicClassFactory,
    CourseFactory,
    ExaminationLevelFactory,
)

from ..models import LearningObjective, SubTopic, Topic


class TopicFactory(DjangoModelFactory):
    class Meta:
        model = Topic

    name = factory.Sequence(lambda n: f"Topic {n}")
    examination_level = factory.SubFactory(ExaminationLevelFactory)
    block_id = factory.Sequence(lambda n: f"block_id_{n}")
    academic_class = factory.SubFactory(AcademicClassFactory)
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyFunction(datetime.now)
    course = factory.SubFactory(CourseFactory)


class SubTopicFactory(DjangoModelFactory):
    class Meta:
        model = SubTopic

    name = factory.Sequence(lambda n: f"SubTopic {n}")
    topic = factory.SubFactory(TopicFactory)
    block_id = factory.Sequence(lambda n: f"sub_block_id_{n}")
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyFunction(datetime.now)


class LearningObjectiveFactory(DjangoModelFactory):
    class Meta:
        model = LearningObjective

    name = factory.Sequence(lambda n: f"Learning Objective {n}")
    block_id = factory.Sequence(lambda n: f"lo_block_id_{n}")
    sub_topic = factory.SubFactory(SubTopicFactory)
