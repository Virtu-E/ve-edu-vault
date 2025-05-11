from typing import Any, Dict, Optional

from src.apps.core.courses.models import ExaminationLevel


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


def find_sequential_path(outline_data, sequential_id, current_path=None):
    """
    Recursively find the path to a sequential block in the course outline

    Args:
        outline_data (dict): Course outline data
        sequential_id (str): ID of the sequential block to find
        current_path (dict): Current path being built (used in recursion)

    Returns:
        dict: Dictionary containing block information organized by category
    """
    if current_path is None:
        current_path = {}

    if outline_data.get("id") and outline_data.get("display_name"):
        block_type = outline_data["category"]
        block_info = {
            "id": outline_data["id"],
            "name": outline_data["display_name"],
            "type": block_type,
        }
        current_path[block_type] = block_info

    if outline_data.get("id") == sequential_id:
        return current_path

    if outline_data.get("child_info") and outline_data["child_info"].get("children"):
        for child in outline_data["child_info"]["children"]:
            # Create a new dictionary for each recursive call
            new_path = current_path.copy()
            result = find_sequential_path(child, sequential_id, new_path)
            if result:
                return result

    return None


def get_iframe_id_from_outline(id_: str, outline: Dict[str, Any]) -> Optional[str]:
    """
    Recursively search the course outline to find the first vertical within a sequential.

    Args:
        id_: The block_id to search for.
        outline: The course outline dictionary containing the course structure.

    Returns:
        Optional[str]: The ID of the first vertical found, or None if not found.
    """
    course_structure = outline.get("course_structure", {})

    def find_sequential(structure: Dict[str, Any]) -> Optional[str]:
        """
        Recursively search through the course structure to find a
        sequential and its first child.

        Args:
            structure: The current structure node being examined.

        Returns:
            Optional[str]: The ID of the first vertical within the
            sequential, or None if not found.
        """
        # If this is the sequential we're looking for, return its first child's ID
        if structure.get("id") == id_:
            children = structure.get("child_info", {}).get("children", [])
            if children:
                return children[0].get("id")
            return None

        # Otherwise, continue searching in children
        child_info = structure.get("child_info", {})
        if child_info:
            children = child_info.get("children", [])
            for child in children:
                result = find_sequential(child)
                if result:
                    return result
        return None

    return find_sequential(course_structure)
