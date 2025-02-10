# TODO : deprecation consideration
def get_sequential_id_from_unit(course_outline, unit_id) -> str:
    """
    Get the sequential (topic ID) ID that contains the given LTI consumer unit.

    Args:
        course_outline (dict): The course outline structure
        unit_id (str): The LTI consumer unit ID to find

    Returns:
        str: The sequential ID if found, None otherwise
    """

    def find_in_structure(structure):
        if structure.get("category") == "sequential":
            verticals = structure.get("child_info", {}).get("children", [])
            for vertical in verticals:
                vertical_children = vertical.get("child_info", {}).get("children", [])
                for child in vertical_children:
                    if child.get("id") == unit_id:
                        return structure.get("id")

        child_info = structure.get("child_info", {})
        if child_info:
            children = child_info.get("children", [])
            for child in children:
                result = find_in_structure(child)
                if result:
                    return result

        return None

    course_structure = course_outline.get("course_structure", {})
    return find_in_structure(course_structure)
