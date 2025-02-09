import logging
from abc import ABC, abstractmethod
from typing import Dict, List

from course_sync.models import ChapterData, CourseStructure, ObjectiveData

log = logging.getLogger(__name__)


class EdxStructureExtractorInterface(ABC):

    @abstractmethod
    def extract(self, structure: Dict) -> CourseStructure:
        raise NotImplementedError()


class StructureExtractor:
    """Responsible for extracting structure components from course data"""

    @staticmethod
    def extract(structure: Dict) -> CourseStructure:
        categories = set()
        topics = set()
        topic_to_category = {}

        try:
            course_data = structure.get("course_structure", {})
            for chapter in course_data.get("child_info", {}).get("children", []):
                chapter_id = chapter.get("id")
                if chapter_id:
                    categories.add(chapter_id)

                if chapter.get("has_children"):
                    for objective in chapter.get("child_info", {}).get("children", []):
                        topic_id = objective.get("id")
                        if topic_id:
                            topics.add(topic_id)
                            topic_to_category[topic_id] = chapter_id

        except Exception as e:
            log.error(f"Error extracting structure components: {e}")
            raise ValueError(f"Invalid course structure format: {e}")

        return CourseStructure(categories, topics, topic_to_category)

    @staticmethod
    def extract_chapters(structure: Dict) -> List[ChapterData]:
        chapters = []
        course_data = structure.get("course_structure", {})

        for chapter in course_data.get("child_info", {}).get("children", []):
            if chapter.get("id"):
                chapters.append(
                    ChapterData(
                        id=chapter["id"],
                        name=chapter["display_name"],
                        objectives=chapter.get("child_info", {}).get("children", []),
                    )
                )
        return chapters

    @staticmethod
    def extract_objectives(chapter: ChapterData) -> List[ObjectiveData]:
        objectives = []
        for obj in chapter.objectives:
            if obj.get("id"):
                objectives.append(ObjectiveData(id=obj["id"], name=obj["display_name"]))
        return objectives
