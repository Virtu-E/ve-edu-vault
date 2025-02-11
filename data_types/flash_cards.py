from pydantic import BaseModel, Field
from pydantic.v1 import validator


class FrontFacingCard(BaseModel):
    title: str
    description: str


class BackFacingCard(BaseModel):
    description: str


class FlashCardQuestion(BaseModel):
    id: str = Field(..., alias="_id")
    topic: str
    academic_class: str
    examination_level: str
    difficulty: str
    front: FrontFacingCard
    back: BackFacingCard

    class Config:
        allow_population_by_field_name = True

    @validator("_id", pre=True, always=True)
    def ensure_string(cls, value):
        return str(value)
