from typing import List

from pydantic import BaseModel, Field


class LearningObjective(BaseModel):
    name: str = Field(..., min_length=1)
    id: str = Field(..., min_length=1)


class TopicData(BaseModel):
    topic_id: str = Field(..., min_length=1)
    topic_name: str = Field(..., min_length=1)
    course_id: str = Field(..., min_length=1)
    course_name: str = Field(..., min_length=1)
    learning_objectives: List[LearningObjective]

    @classmethod
    def from_api_response(cls, data: dict) -> "TopicData":
        """Create TopicData from API response"""
        return cls(
            topic_id=data["topic_id"],
            topic_name=data["topic_name"],
            course_id=data["course_id"],
            course_name=data["course_name"],
            learning_objectives=[
                LearningObjective(name=obj["name"], id=obj["id"])
                for obj in data.get("learning_objectives", [])
            ],
        )
