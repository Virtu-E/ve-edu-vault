from dataclasses import dataclass
from typing import Dict, List, Set


@dataclass
class CourseStructure:
    """Value object representing course structure data"""

    categories: Set[str]
    topics: Set[str]
    topic_to_category: Dict[str, str]


@dataclass
class ChapterData:
    """Value object for chapter/category data"""

    id: str
    name: str
    objectives: List[Dict]


@dataclass
class ObjectiveData:
    """Value object for objective/topic data"""

    id: str
    name: str
