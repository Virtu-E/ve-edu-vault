import factory
from bson import ObjectId
from factory import Dict, Factory, Faker, List, SubFactory

from data_types.ai_core import (Attempt, DifficultyStats, ModeData,
                                QuestionAIContext)


class AttemptsFactory(Factory):
    class Meta:
        model = Attempt

    success = Faker("boolean")
    timeSpent = Faker("random_int", min=1, max=60)
    attemptNumber = Faker("random_int", min=1, max=3)


class QuestionAIContextFactory(Factory):
    class Meta:
        model = QuestionAIContext

    attempts = SubFactory(AttemptsFactory)
    _id = factory.LazyFunction(lambda: str(ObjectId()))
    difficulty: str
    tags = factory.List([factory.Faker("word") for _ in range(3)])
    difficulty = factory.Faker("word")


class DifficultyStatsFactory(Factory):
    class Meta:
        model = DifficultyStats

    totalAttempts = Faker("random_int", min=1, max=100)
    successRate = Faker("pyfloat", min_value=0, max_value=1)
    averageTime = Faker("pyfloat", min_value=1, max_value=60)
    failedTags = List(["algebra", "geometry"])
    firstAttemptSuccessRate = Faker("pyfloat", min_value=0, max_value=1)
    secondAttemptSuccessRate = Faker("pyfloat", min_value=0, max_value=1)
    thirdAttemptSuccessRate = Faker("pyfloat", min_value=0, max_value=1)
    averageAttemptsToSuccess = Faker("pyfloat", min_value=1, max_value=3)
    completionRate = Faker("pyfloat", min_value=0, max_value=1)
    incompleteRate = Faker("pyfloat", min_value=0, max_value=1)
    earlyAbandonment = Faker("pyfloat", min_value=0, max_value=1)
    averageFirstAttemptTime = Faker("pyfloat", min_value=1, max_value=60)
    averageSecondAttemptTime = Faker("pyfloat", min_value=1, max_value=60)
    averageThirdAttemptTime = Faker("pyfloat", min_value=1, max_value=60)
    timeDistribution = Dict({"1": 0.5, "2": 0.3, "3": 0.2})


class ModeDataFactory(Factory):
    class Meta:
        model = ModeData

    questions = List([SubFactory(QuestionAIContextFactory) for _ in range(2)])
    difficultyStats = Dict({"easy": SubFactory(DifficultyStatsFactory)})
