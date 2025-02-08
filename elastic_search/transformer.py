from abc import ABC, abstractmethod
from typing import Any, List

from data_types.elastic_search import LearningObjective, TopicData


class DataTransformer(ABC):
    @abstractmethod
    def transform(self, data: Any) -> List[TopicData]:
        pass


class ElasticTransformer(DataTransformer):
    def transform(self, data: Any) -> List[TopicData]:
        blocks = data["blocks"]

        # Find the course block
        course_block = next(
            block for block in blocks.values() if block["type"] == "course"
        )

        # Find all chapter blocks that represent topics
        topic_blocks = [
            block
            for block in blocks.values()
            if block["type"] == "chapter" and block["id"] in course_block["children"]
        ]

        result = []
        for topic in topic_blocks:
            # Get learning objectives (sequential blocks) for this topic
            objectives = []
            for child_id in topic["children"]:
                objective = blocks[child_id]
                objectives.append(
                    LearningObjective(
                        name=objective["display_name"], id=objective["id"]
                    )
                )

            topic_data = TopicData(
                topic_name=topic["display_name"],
                topic_id=topic["id"],
                course_id=course_block["id"],
                course_name=course_block["display_name"],
                learning_objectives=objectives,
            )
            result.append(topic_data)

        return result
