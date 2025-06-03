from enum import Enum
from typing import Dict, Type

from .grader_types.base import AbstractQuestionGrader
from .grader_types.fill_in_blank import FillInTheBlankGrader
from .grader_types.multiple_choice import MultipleChoiceGrader


class GraderTypeEnum(Enum):
    MULTIPLE_CHOICE = "multiple-choice"
    FILL_IN_BLANKS = "fill-in-the-blank"


class GraderFactory:
    _graders: Dict[GraderTypeEnum, Type[AbstractQuestionGrader]] = {}

    @classmethod
    def register_grader(
        cls, question_type: GraderTypeEnum, grader_class: Type[AbstractQuestionGrader]
    ) -> None:
        """Register a grader class for a specific question type"""
        cls._graders[question_type] = grader_class

    @classmethod
    def get_grader(cls, question_type: str) -> AbstractQuestionGrader:
        """Get an instance of the appropriate grader for a question type"""
        try:
            enum_type = GraderTypeEnum(question_type)
        except ValueError:
            raise ValueError(f"Invalid question type: {question_type}")

        grader_class = cls._graders.get(enum_type)
        if not grader_class:
            raise ValueError(f"No grader registered for question type: {question_type}")
        return grader_class()


GraderFactory.register_grader(GraderTypeEnum.MULTIPLE_CHOICE, MultipleChoiceGrader)
GraderFactory.register_grader(GraderTypeEnum.FILL_IN_BLANKS, FillInTheBlankGrader)
