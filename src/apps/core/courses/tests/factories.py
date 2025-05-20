import factory.fuzzy
from factory.django import DjangoModelFactory

from ..models import AcademicClass, Course, ExaminationLevel, ExaminationLevelChoices


class ExaminationLevelFactory(DjangoModelFactory):
    class Meta:
        model = ExaminationLevel
        django_get_or_create = ("name",)

    name = factory.Iterator([choice.value for choice in ExaminationLevelChoices])


class AcademicClassFactory(DjangoModelFactory):
    class Meta:
        model = AcademicClass
        django_get_or_create = ("name",)

    name = factory.Iterator(["Form 1", "Form 2", "Form 3", "Form 4"])


class CourseFactory(DjangoModelFactory):
    class Meta:
        model = Course
        django_get_or_create = ("course_key",)

    name = factory.Sequence(lambda n: f"Course {n}")
    course_key = factory.Sequence(lambda n: f"course-v1:VirtuEducate+C{n}+2023")
    course_outline = factory.LazyFunction(
        lambda: {
            "blocks": {
                "section1": {"display_name": "Section 1"},
                "section2": {"display_name": "Section 2"},
            }
        }
    )
