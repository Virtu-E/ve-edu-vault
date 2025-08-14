import uuid

import factory
import factory.fuzzy

from src.apps.learning_tools.assessments.services.data_types import (
    GradedFeedback, GradedResponseSchema, GradingRequest, StudentAnswer)


class StudentAnswerFactory(factory.Factory):
    class Meta:
        model = StudentAnswer

    question_type = factory.fuzzy.FuzzyChoice(
        ["multiple_choice", "free_response", "numeric", "matching"]
    )
    question_metadata = factory.Dict(
        {
            "question_text": factory.Faker("sentence"),
            "difficulty": factory.fuzzy.FuzzyChoice(["easy", "medium", "hard"]),
            "topic": factory.Faker("word"),
        }
    )


class MultipleChoiceAnswerFactory(StudentAnswerFactory):
    question_type = "multiple_choice"
    question_metadata = factory.Dict(
        {
            "choices": ["Option 1", "Option 2", "Option 3", "Option 4"],
            "selected_choice": factory.LazyFunction(
                lambda: factory.random.randgen.choice(
                    ["Option 1", "Option 2", "Option 3", "Option 4"]
                )
            ),
            "correct_choice": "Option 1",
        }
    )


class FreeResponseAnswerFactory(StudentAnswerFactory):
    question_type = "free_response"
    question_metadata = factory.Dict(
        {
            "response": factory.Faker("paragraph"),
            "keywords": factory.List([factory.Faker("word") for _ in range(3)]),
        }
    )


class NumericAnswerFactory(StudentAnswerFactory):
    question_type = "numeric"
    question_metadata = factory.Dict(
        {
            "answer": factory.fuzzy.FuzzyFloat(0, 100),
            "correct_answer": 42.0,
            "tolerance": 0.01,
        }
    )


class GradedFeedbackFactory(factory.Factory):
    class Meta:
        model = GradedFeedback

    message = factory.Faker("sentence")
    explanation = factory.Maybe(
        factory.fuzzy.FuzzyChoice([True, False]),
        yes_declaration=factory.Faker("paragraph"),
        no_declaration=None,
    )
    steps = factory.Maybe(
        factory.fuzzy.FuzzyChoice([True, False]),
        yes_declaration=factory.List([factory.Faker("sentence") for _ in range(3)]),
        no_declaration=None,
    )
    hint = factory.Maybe(
        factory.fuzzy.FuzzyChoice([True, False]),
        yes_declaration=factory.Faker("sentence"),
        no_declaration=None,
    )
    show_solution = factory.fuzzy.FuzzyChoice([True, False])
    misconception = factory.Maybe(
        factory.fuzzy.FuzzyChoice([True, False]),
        yes_declaration=factory.Faker("sentence"),
        no_declaration=None,
    )


class CorrectFeedbackFactory(GradedFeedbackFactory):
    message = factory.fuzzy.FuzzyChoice(
        ["Correct!", "Great job!", "Well done!", "That's right!", "Perfect!"]
    )
    show_solution = False


class IncorrectFeedbackFactory(GradedFeedbackFactory):
    message = factory.fuzzy.FuzzyChoice(
        [
            "Incorrect. Try again.",
            "Not quite right.",
            "That's not the correct answer.",
            "Please try again.",
        ]
    )


class FeedbackWithStepsFactory(GradedFeedbackFactory):
    message = "Here's how to solve this problem:"
    steps = factory.List([factory.Faker("sentence") for _ in range(3)])
    show_solution = True


class GradedResponseFactory(factory.Factory):
    class Meta:
        model = GradedResponseSchema

    question_metadata = factory.Dict(
        {
            "question_text": factory.Faker("sentence"),
            "difficulty": factory.fuzzy.FuzzyChoice(["easy", "medium", "hard"]),
            "topic": factory.Faker("word"),
        }
    )
    is_correct = factory.fuzzy.FuzzyChoice([True, False])
    score = factory.LazyAttribute(
        lambda o: 1.0 if o.is_correct else factory.fuzzy.FuzzyFloat(0, 0.9).fuzz()
    )
    feedback = factory.SubFactory(GradedFeedbackFactory)
    attempts_remaining = factory.fuzzy.FuzzyInteger(0, 3)
    question_type = factory.fuzzy.FuzzyChoice(
        ["multiple_choice", "free_response", "numeric", "matching"]
    )


class GradingRequestFactory(factory.Factory):
    class Meta:
        model = GradingRequest

    question_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    attempted_answer = factory.SubFactory(StudentAnswerFactory)
