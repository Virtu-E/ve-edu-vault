from typing import Dict, Type

from .qn_graders import AbstractQuestionGrader, MultipleChoiceGrader


class GraderFactory:
    _graders: Dict[str, Type[AbstractQuestionGrader]] = {}

    @classmethod
    def register_grader(
        cls, question_type: str, grader_class: Type[AbstractQuestionGrader]
    ) -> None:
        """Register a grader class for a specific question type"""
        cls._graders[question_type] = grader_class

    @classmethod
    def get_grader(cls, question_type: str) -> AbstractQuestionGrader:
        """Get an instance of the appropriate grader for a question type"""
        grader_class = cls._graders.get(question_type)
        if not grader_class:
            raise ValueError(f"No grader registered for question type: {question_type}")
        return grader_class()


GraderFactory.register_grader("multiple-choice", MultipleChoiceGrader)
