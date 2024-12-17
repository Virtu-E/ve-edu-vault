from dataclasses import dataclass


# TODO : turn into pydantic classes
@dataclass
class PerformanceStats:
    """Data class to store performance statistics."""

    ranked_difficulties: list[tuple[str, float]]
    difficulty_status: dict[str, str]
