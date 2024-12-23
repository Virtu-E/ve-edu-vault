from pydantic.v1 import BaseModel


class EdxUserData(BaseModel):
    id: int
    username: str
    email: str
    course_key: str
