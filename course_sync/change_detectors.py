from abc import abstractmethod
from typing import Dict

from course_sync.extractor import StructureExtractor


class ChangeDetector:
    """Base class for detecting changes in course structure"""

    @abstractmethod
    def detect_changes(self, stored: Dict, new: Dict) -> bool:
        pass


class StructuralChangeDetector(ChangeDetector):
    def detect_changes(self, stored: Dict, new: Dict) -> bool:
        stored_struct = StructureExtractor.extract(stored)
        new_struct = StructureExtractor.extract(new)
        return stored_struct.categories != new_struct.categories or stored_struct.topics != new_struct.topics


class NameChangeDetector(ChangeDetector):
    def detect_changes(self, stored: Dict, new: Dict) -> bool:
        stored_name = stored.get("course_structure", {}).get("display_name")
        new_name = new.get("course_structure", {}).get("display_name")
        return stored_name != new_name


class CategoryNameChangeDetector(ChangeDetector):
    def detect_changes(self, stored: Dict, new: Dict) -> bool:
        stored_chapters = {chapter["id"]: chapter["display_name"] for chapter in stored.get("course_structure", {}).get("child_info", {}).get("children", []) if chapter.get("id")}

        new_chapters = {chapter["id"]: chapter["display_name"] for chapter in new.get("course_structure", {}).get("child_info", {}).get("children", []) if chapter.get("id")}

        return stored_chapters != new_chapters


class TopicNameChangeDetector(ChangeDetector):
    def detect_changes(self, stored: Dict, new: Dict) -> bool:
        stored_topics = self._extract_topics(stored)
        new_topics = self._extract_topics(new)
        return stored_topics != new_topics

    def _extract_topics(self, structure: Dict) -> Dict[str, str]:
        topics = {}
        course_data = structure.get("course_structure", {})
        for chapter in course_data.get("child_info", {}).get("children", []):
            if chapter.get("has_children"):
                for objective in chapter.get("child_info", {}).get("children", []):
                    if objective.get("id"):
                        topics[objective["id"]] = objective["display_name"]
        return topics
