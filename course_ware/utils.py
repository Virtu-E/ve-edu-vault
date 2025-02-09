from course_ware.models import ExaminationLevel


def academic_class_from_course_id(course_id: str) -> str | None:
    """
    Function to get Academic class from course id
    """
    parts = course_id.split(":")

    course_parts = parts[-1].split("+")

    program = course_parts[1]
    number = course_parts[2]

    first_digit = int(number[0])

    if program == "MSCE":
        if first_digit == 3:
            return "Form 3"
        if first_digit == 4:
            return "Form 4"
    elif program == "JCE":
        if first_digit == 1:
            return "Form 1"
        elif first_digit == 2:
            return "Form 2"

    return None


def get_examination_level_from_course_id(course_id: str) -> ExaminationLevel:
    """
    Function to get examination level from course id
    """
    parts = course_id.split(":")

    course_parts = parts[-1].split("+")
    return ExaminationLevel.objects.get(name=course_parts[1])
