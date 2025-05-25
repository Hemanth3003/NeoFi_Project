from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..database import get_db
from ..schemas.version import EventVersion, VersionDiff
from ..models.version import EventVersion as EventVersionModel
from ..models.event import Event as EventModel
from ..models.permission import Permission as PermissionModel
from ..schemas.permission import RoleEnum
from ..models.user import User as UserModel
from ..utils.auth import get_current_active_user
from ..utils.diff import generate_diff

router = APIRouter(
    prefix="/api/events",
    tags=["versions"]
)

def check_event_access(db: Session, event_id: int, user_id: int):
    """Check if user has access to the event"""
    permission = db.query(PermissionModel).filter(
        PermissionModel.event_id == event_id,
        PermissionModel.user_id == user_id
    ).first()
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this event"
        )
    return permission

def check_event_edit_access(db: Session, event_id: int, user_id: int):
    """Check if user has edit access to the event"""
    permission = db.query(PermissionModel).filter(
        PermissionModel.event_id == event_id,
        PermissionModel.user_id == user_id,
        PermissionModel.role.in_([RoleEnum.owner.value, RoleEnum.editor.value])
    ).first()
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have edit access to this event"
        )
    return permission

@router.get("/{event_id}/history/{version_id}", response_model=EventVersion)
def get_event_version(
    event_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Check if user has access to the event
    check_event_access(db, event_id, current_user.id)
    
    # Get the specific version
    version = db.query(EventVersionModel).filter(
        EventVersionModel.event_id == event_id,
        EventVersionModel.id == version_id
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return version

@router.post("/{event_id}/rollback/{version_id}", response_model=EventVersion)
def rollback_event(
    event_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Check if user has edit access to the event
    check_event_edit_access(db, event_id, current_user.id)
    
    # Get the event
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Get the version to rollback to
    version = db.query(EventVersionModel).filter(
        EventVersionModel.event_id == event_id,
        EventVersionModel.id == version_id
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Update the event with the version data
    version_data = version.data
    
    # Extract the fields we can update
    event.title = version_data.get("title", event.title)
    event.description = version_data.get("description", event.description)
    
    # Handle datetime fields carefully
    if "start_time" in version_data:
        event.start_time = datetime.fromisoformat(version_data["start_time"])
    if "end_time" in version_data:
        event.end_time = datetime.fromisoformat(version_data["end_time"])
    
    event.location = version_data.get("location", event.location)
    event.is_recurring = version_data.get("is_recurring", event.is_recurring)
    event.recurrence_pattern = version_data.get("recurrence_pattern", event.recurrence_pattern)
    
    db.commit()
    
    # Create a new version to record the rollback
    new_version = EventVersionModel(
        event_id=event_id,
        created_by=current_user.id,
        data={
            "title": event.title,
            "description": event.description,
            "start_time": event.start_time.isoformat(),
            "end_time": event.end_time.isoformat(),
            "location": event.location,
            "is_recurring": event.is_recurring,
            "recurrence_pattern": event.recurrence_pattern
        },
        change_description=f"Rolled back to version {version_id}"
    )
    
    db.add(new_version)
    db.commit()
    db.refresh(new_version)
    
    return new_version

@router.get("/{event_id}/changelog", response_model=List[EventVersion])
def get_event_changelog(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Check if user has access to the event
    check_event_access(db, event_id, current_user.id)
    
    # Get all versions for the event, ordered by creation time
    versions = db.query(EventVersionModel).filter(
        EventVersionModel.event_id == event_id
    ).order_by(EventVersionModel.created_at.desc()).all()
    
    return versions

@router.get("/{event_id}/diff/{version_id1}/{version_id2}", response_model=VersionDiff)
def get_version_diff(
    event_id: int,
    version_id1: int,
    version_id2: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Check if user has access to the event
    check_event_access(db, event_id, current_user.id)
    
    # Get both versions
    version1 = db.query(EventVersionModel).filter(
        EventVersionModel.event_id == event_id,
        EventVersionModel.id == version_id1
    ).first()
    
    version2 = db.query(EventVersionModel).filter(
        EventVersionModel.event_id == event_id,
        EventVersionModel.id == version_id2
    ).first()
    
    if not version1 or not version2:
        raise HTTPException(status_code=404, detail="One or both versions not found")
    
    # Generate diff between versions
    changes = generate_diff(version1.data, version2.data)
    
    return {
        "version1_id": version_id1,
        "version2_id": version_id2,
        "changes": changes
    }