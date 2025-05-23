from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class WebhookRequest(BaseModel):
    event_type: str
    event_id: str
    timestamp: Optional[datetime] = None
    data: Dict[str, Any]

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
