from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class RoleEnum(str, Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"

class PermissionBase(BaseModel):
    role: RoleEnum

class PermissionCreate(PermissionBase):
    user_id: int

class PermissionUpdate(PermissionBase):
    pass

class PermissionInDB(PermissionBase):
    id: int
    event_id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class Permission(PermissionInDB):
    pass

class ShareEvent(BaseModel):
    users: List[PermissionCreate]