from datetime import datetime

import factory.fuzzy

from src.repository.graded_responses.data_types import GradedFeedback, GradedResponse


class ResponseFeedbackFactory(factory.Factory):
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


class PositiveResponseFeedbackFactory(ResponseFeedbackFactory):
    message = factory.fuzzy.FuzzyChoice(
        ["Good job!", "Great work!", "Well done!", "Excellent!", "Perfect!"]
    )
    explanation = "Your answer demonstrates understanding."
    steps = ["Step 1", "Step 2"]
    hint = None
    show_solution = False
    misconception = None


class NegativeResponseFeedbackFactory(ResponseFeedbackFactory):
    message = factory.fuzzy.FuzzyChoice(
        ["Try again.", "Not quite right.", "Incorrect.", "Review and try again."]
    )
    explanation = "Consider reviewing the formula."
    steps = None
    hint = "Look at the units."
    show_solution = False
    misconception = "Common confusion between mass and weight."


class QuestionAttemptFactory(factory.Factory):
    class Meta:
        model = GradedResponse

    question_id = factory.Sequence(lambda n: f"q{n+1}")
    user_id = factory.fuzzy.FuzzyInteger(10000, 99999)
    attempts_remaining = factory.fuzzy.FuzzyInteger(0, 3)
    created_at = factory.LazyFunction(datetime.now)
    feedback = factory.SubFactory(ResponseFeedbackFactory)
    grading_version = "1.0"
    is_correct = factory.fuzzy.FuzzyChoice([True, False])
    question_metadata = factory.Dict(
        {
            "difficulty": factory.fuzzy.FuzzyChoice(["easy", "medium", "hard"]),
            "topic": factory.Faker("word"),
        }
    )
    question_type = factory.fuzzy.FuzzyChoice(
        ["multiple_choice", "free_response", "numeric", "matching"]
    )
    score = factory.LazyAttribute(lambda o: 10.0 if o.is_correct else 0.0)


class CorrectQuestionAttemptFactory(QuestionAttemptFactory):
    is_correct = True
    score = 10.0
    feedback = factory.SubFactory(PositiveResponseFeedbackFactory)
    question_type = "multiple-choice"


class IncorrectQuestionAttemptFactory(QuestionAttemptFactory):
    is_correct = False
    score = 0.0
    feedback = factory.SubFactory(NegativeResponseFeedbackFactory)
    question_type = "numeric"
