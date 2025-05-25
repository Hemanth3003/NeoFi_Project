from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..schemas.event import Event, EventCreate, EventUpdate, EventBatchCreate
from ..models.event import Event as EventModel
from ..models.permission import Permission as PermissionModel
from ..models.version import EventVersion as EventVersionModel
from ..schemas.permission import RoleEnum
from ..models.user import User as UserModel
from ..utils.auth import get_current_active_user

router = APIRouter(
    prefix="/api/events",
    tags=["events"]
)

def check_event_access(db: Session, event_id: int, user_id: int, required_roles: List[str]):
    """Check if user has required access to the event"""
    permission = db.query(PermissionModel).filter(
        PermissionModel.event_id == event_id,
        PermissionModel.user_id == user_id
    ).first()
    
    if not permission or permission.role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return permission

def check_event_conflicts(db: Session, start_time: datetime, end_time: datetime, 
                         user_id: int, exclude_event_id: Optional[int] = None):
    """Check for conflicting events"""
    query = db.query(EventModel).join(
        PermissionModel, EventModel.id == PermissionModel.event_id
    ).filter(
        PermissionModel.user_id == user_id,
        # Event starts during another event
        ((EventModel.start_time <= start_time) & (EventModel.end_time > start_time)) |
        # Event ends during another event
        ((EventModel.start_time < end_time) & (EventModel.end_time >= end_time)) |
        # Event completely contains another event
        ((EventModel.start_time >= start_time) & (EventModel.end_time <= end_time))
    )
    
    if exclude_event_id:
        query = query.filter(EventModel.id != exclude_event_id)
    
    conflicts = query.all()
    return conflicts

def create_event_version(db: Session, event_id: int, user_id: int, data: dict, description: str = None):
    """Create a new version of an event"""
    version = EventVersionModel(
        event_id=event_id,
        created_by=user_id,
        data=data,
        change_description=description
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version

@router.post("", response_model=Event)
def create_event(
    event: EventCreate, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    force_create: bool = Query(False, description="Create event even if conflicts exist")
):
    # Check for conflicts
    conflicts = check_event_conflicts(
        db, event.start_time, event.end_time, current_user.id
    )
    
    if conflicts and not force_create:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Event conflicts with {len(conflicts)} existing events"
        )
    
    # Create the event
    db_event = EventModel(
        title=event.title,
        description=event.description,
        start_time=event.start_time,
        end_time=event.end_time,
        location=event.location,
        is_recurring=event.is_recurring,
        recurrence_pattern=event.recurrence_pattern,
        owner_id=current_user.id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    
    # Create owner permission
    permission = PermissionModel(
        event_id=db_event.id,
        user_id=current_user.id,
        role=RoleEnum.owner.value
    )
    db.add(permission)
    
    # Create initial version
    create_event_version(
        db, 
        db_event.id, 
        current_user.id, 
        {
            "title": db_event.title,
            "description": db_event.description,
            "start_time": db_event.start_time.isoformat(),
            "end_time": db_event.end_time.isoformat(),
            "location": db_event.location,
            "is_recurring": db_event.is_recurring,
            "recurrence_pattern": db_event.recurrence_pattern
        },
        "Event created"
    )
    
    db.commit()
    return db_event

@router.get("", response_model=List[Event])
def get_events(
    skip: int = 0, 
    limit: int = 100,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Get all events where user has any permission
    query = db.query(EventModel).join(
        PermissionModel, EventModel.id == PermissionModel.event_id
    ).filter(
        PermissionModel.user_id == current_user.id
    )
    
    # Apply date filters if provided
    if start_date:
        query = query.filter(EventModel.end_time >= start_date)
    if end_date:
        query = query.filter(EventModel.start_time <= end_date)
    
    events = query.offset(skip).limit(limit).all()
    return events

@router.get("/{event_id}", response_model=Event)
def get_event(
    event_id: int, 
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Check if user has access to the event (any role)
    check_event_access(db, event_id, current_user.id, 
                      [RoleEnum.owner.value, RoleEnum.editor.value, RoleEnum.viewer.value])
    
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event

@router.put("/{event_id}", response_model=Event)
def update_event(
    event_id: int,
    event_update: EventUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    force_update: bool = Query(False, description="Update event even if conflicts exist")
):
    # Check if user has edit access to the event
    check_event_access(db, event_id, current_user.id, [RoleEnum.owner.value, RoleEnum.editor.value])
    
    # Get the existing event
    db_event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Store original data for versioning
    original_data = {
        "title": db_event.title,
        "description": db_event.description,
        "start_time": db_event.start_time.isoformat(),
        "end_time": db_event.end_time.isoformat(),
        "location": db_event.location,
        "is_recurring": db_event.is_recurring,
        "recurrence_pattern": db_event.recurrence_pattern
    }
    
    # Check for conflicts if times are being updated
    if event_update.start_time or event_update.end_time:
        start_time = event_update.start_time or db_event.start_time
        end_time = event_update.end_time or db_event.end_time
        
        conflicts = check_event_conflicts(
            db, start_time, end_time, current_user.id, exclude_event_id=event_id
        )
        
        if conflicts and not force_update:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Event update conflicts with {len(conflicts)} existing events"
            )
    
    # Update event fields
    update_data = event_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)
    
    db.commit()
    db.refresh(db_event)
    
    # Create new version
    new_data = {
        "title": db_event.title,
        "description": db_event.description,
        "start_time": db_event.start_time.isoformat(),
        "end_time": db_event.end_time.isoformat(),
        "location": db_event.location,
        "is_recurring": db_event.is_recurring,
        "recurrence_pattern": db_event.recurrence_pattern
    }
    
    create_event_version(
        db, 
        event_id, 
        current_user.id, 
        new_data,
        "Event updated"
    )
    
    return db_event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Check if user has owner access to the event
    check_event_access(db, event_id, current_user.id, [RoleEnum.owner.value])
    
    # Get the event
    db_event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Delete the event (and related records through cascade)
    db.delete(db_event)
    db.commit()
    
    return None

@router.post("/batch", response_model=List[Event])
def create_batch_events(
    batch: EventBatchCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
    force_create: bool = Query(False, description="Create events even if conflicts exist")
):
    # Check for conflicts for all events
    all_conflicts = []
    for idx, event in enumerate(batch.events):
        conflicts = check_event_conflicts(
            db, event.start_time, event.end_time, current_user.id
        )
        if conflicts:
            all_conflicts.append((idx, conflicts))
    
    if all_conflicts and not force_create:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Found conflicts for {len(all_conflicts)} events in batch"
        )
    
    # Create all events in a transaction
    created_events = []
    for event in batch.events:
        db_event = EventModel(
            title=event.title,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            location=event.location,
            is_recurring=event.is_recurring,
            recurrence_pattern=event.recurrence_pattern,
            owner_id=current_user.id
        )
        db.add(db_event)
        db.flush()  # Get ID without committing
        
        # Create owner permission
        permission = PermissionModel(
            event_id=db_event.id,
            user_id=current_user.id,
            role=RoleEnum.owner.value
        )
        db.add(permission)
        
        # Create initial version
        event_data = {
            "title": db_event.title,
            "description": db_event.description,
            "start_time": db_event.start_time.isoformat(),
            "end_time": db_event.end_time.isoformat(),
            "location": db_event.location,
            "is_recurring": db_event.is_recurring,
            "recurrence_pattern": db_event.recurrence_pattern
        }
        
        version = EventVersionModel(
            event_id=db_event.id,
            created_by=current_user.id,
            data=event_data,
            change_description="Event created in batch"
        )
        db.add(version)
        
        created_events.append(db_event)
    
    db.commit()
    return created_events