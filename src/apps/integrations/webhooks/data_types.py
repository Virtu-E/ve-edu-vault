from datetime import datetime
from typing import Optional

from pydantic import BaseModel


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
