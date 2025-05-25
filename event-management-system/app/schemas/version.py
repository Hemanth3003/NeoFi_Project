from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class EventVersionBase(BaseModel):
    data: Dict[str, Any]
    change_description: Optional[str] = None

class EventVersionCreate(EventVersionBase):
    pass

class EventVersionInDB(EventVersionBase):
    id: int
    event_id: int
    created_by: int
    created_at: datetime

    class Config:
        orm_mode = True

class EventVersion(EventVersionInDB):
    pass

class EventDiff(BaseModel):
    field: str
    old_value: Any
    new_value: Any

class VersionDiff(BaseModel):
    version1_id: int
    version2_id: int
    changes: List[EventDiff]