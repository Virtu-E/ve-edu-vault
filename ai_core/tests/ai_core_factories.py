import factory
from bson import ObjectId
from factory import Factory, SubFactory

from data_types.ai_core import QuestionAIContext, Attempt


class AttemptsFactory(Factory):
    class Meta:
        model = Attempt

    attemptNumber = 1
    success = False
    timeSpent = 90


class QuestionAIContextFactory(Factory):
    class Meta:
        model = QuestionAIContext

    attempts = SubFactory(AttemptsFactory)
    _id = factory.LazyFunction(lambda: str(ObjectId()))
    difficulty: str
    tags = factory.List([factory.Faker("word") for _ in range(3)])
    difficulty = factory.Faker("word")
