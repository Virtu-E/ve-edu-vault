import uuid
from datetime import datetime

import factory.fuzzy

from src.repository.question_repository.data_types import (Content, Option,
                                                           Question, Solution)


class OptionFactory(factory.Factory):
    class Meta:
        model = Option

    id = factory.Sequence(lambda n: f"option{n+1}")
    text = factory.Faker("sentence")
    is_correct = factory.fuzzy.FuzzyChoice([True, False])


class CorrectOptionFactory(OptionFactory):
    is_correct = True


class IncorrectOptionFactory(OptionFactory):
    is_correct = False


class ContentFactory(factory.Factory):
    class Meta:
        model = Content

    options = factory.List(
        [
            factory.SubFactory(
                CorrectOptionFactory, id="option1", text="Correct option 1"
            ),
            factory.SubFactory(
                IncorrectOptionFactory, id="option2", text="Incorrect option 1"
            ),
            factory.SubFactory(
                IncorrectOptionFactory, id="option3", text="Incorrect option 2"
            ),
            factory.SubFactory(
                CorrectOptionFactory, id="option4", text="Correct option 2"
            ),
        ]
    )


class NoCorrectOptionsContentFactory(ContentFactory):
    options = factory.List(
        [
            factory.SubFactory(
                IncorrectOptionFactory, id="option1", text="Incorrect option 1"
            ),
            factory.SubFactory(
                IncorrectOptionFactory, id="option2", text="Incorrect option 2"
            ),
        ]
    )


class EmptyOptionsContentFactory(ContentFactory):
    options = factory.List([])


class SolutionFactory(factory.Factory):
    class Meta:
        model = Solution

    explanation = factory.Faker("paragraph")
    steps = factory.List(
        ["Step 1: Understand the question", "Step 2: Identify the correct options"]
    )


class QuestionFactory(factory.Factory):
    class Meta:
        model = Question

    _id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    category_id = factory.Sequence(lambda n: f"category{n+1}")
    text = factory.Faker("sentence")
    topic = "Mathematics"
    sub_topic = "Algebra"
    learning_objective = "Understand basic algebraic principles"
    academic_class = "Grade 10"
    examination_level = "High School"
    difficulty = factory.fuzzy.FuzzyChoice(["Easy", "Medium", "Hard"])
    tags = ["algebra", "mathematics", "multiple-choice"]
    question_type = "multiple-choice"
    content = factory.SubFactory(ContentFactory)
    solution = factory.SubFactory(SolutionFactory)
    hint = "Think about the properties of equations."
    possible_misconception = "Students often confuse the order of operations."
    created_at = factory.LazyFunction(datetime.now)
    updated_at = factory.LazyFunction(datetime.now)


class NoCorrectOptionsQuestionFactory(QuestionFactory):
    topic = "Logic"
    sub_topic = "Critical Thinking"
    learning_objective = "Identify logical fallacies"
    academic_class = "Grade 11"
    difficulty = "Hard"
    tags = ["logic", "critical-thinking"]
    content = factory.SubFactory(NoCorrectOptionsContentFactory)
    solution = factory.SubFactory(
        SolutionFactory,
        explanation="This is a trick question with no correct answers.",
        steps=["Step 1: Recognize there are no correct options"],
    )
    hint = "Think carefully about each statement."
    possible_misconception = (
        "Students often assume at least one option must be correct."
    )


class TrueFalseQuestionFactory(QuestionFactory):
    text = "The statement is true."
    topic = "General Knowledge"
    sub_topic = "True/False"
    learning_objective = "Test basic knowledge"
    academic_class = "Grade 9"
    examination_level = "Middle School"
    difficulty = "Easy"
    tags = ["true-false", "basic"]
    content = factory.LazyFunction(
        lambda: Content(
            options=[
                Option(id="true", text="True", is_correct=True),
                Option(id="false", text="False", is_correct=False),
            ]
        )
    )
    solution = factory.SubFactory(
        SolutionFactory,
        explanation="The statement is true because...",
        steps=["Step 1: Analyze the statement"],
    )
    hint = "Think about the definition."
    possible_misconception = "Students might misinterpret the statement."
