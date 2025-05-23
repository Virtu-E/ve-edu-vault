from datetime import datetime
from typing import Optional

from pydantic import BaseModel

# TODO : this can be streamlined to fit a general purpose use.
# Right now, its tightly coupled to edx events


class RequestMetaData(BaseModel):
    event_type: str


class WebHookData(BaseModel):
    course_key: str
    display_name: Optional[str] = None


class WebhookRequestData(BaseModel):
    metadata: RequestMetaData
    data: WebHookData
    event_id: str
    timestamp: datetime
