from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas.permission import Permission, PermissionCreate, PermissionUpdate, ShareEvent, RoleEnum
from ..models.permission import Permission as PermissionModel
from ..models.event import Event as EventModel
from ..models.user import User as UserModel
from ..utils.auth import get_current_active_user

router = APIRouter(
    prefix="/api/events",
    tags=["collaboration"]
)

def check_event_ownership(db: Session, event_id: int, user_id: int):
    """Check if user is the owner of the event"""
    permission = db.query(PermissionModel).filter(
        PermissionModel.event_id == event_id,
        PermissionModel.user_id == user_id,
        PermissionModel.role == RoleEnum.owner.value
    ).first()
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can manage permissions"
        )
    return permission

@router.post("/{event_id}/share", response_model=List[Permission])
def share_event(
    event_id: int,
    share_data: ShareEvent,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Check if event exists
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if current user is the owner
    check_event_ownership(db, event_id, current_user.id)
    
    # Create permissions for each user
    created_permissions = []
    for user_perm in share_data.users:
        # Check if user exists
        user = db.query(UserModel).filter(UserModel.id == user_perm.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User with ID {user_perm.user_id} not found")
        
        # Check if permission already exists
        existing_perm = db.query(PermissionModel).filter(
            PermissionModel.event_id == event_id,
            PermissionModel.user_id == user_perm.user_id
        ).first()
        
        if existing_perm:
            # Update existing permission
            existing_perm.role = user_perm.role
            db.commit()
            db.refresh(existing_perm)
            created_permissions.append(existing_perm)
        else:
            # Create new permission
            new_perm = PermissionModel(
                event_id=event_id,
                user_id=user_perm.user_id,
                role=user_perm.role
            )
            db.add(new_perm)
            db.commit()
            db.refresh(new_perm)
            created_permissions.append(new_perm)
    
    return created_permissions

@router.get("/{event_id}/permissions", response_model=List[Permission])
def get_event_permissions(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Check if event exists
    event = db.query(EventModel).filter(EventModel.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if user has access to the event
    user_perm = db.query(PermissionModel).filter(
        PermissionModel.event_id == event_id,
        PermissionModel.user_id == current_user.id
    ).first()
    
    if not user_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this event"
        )
    
    # Get all permissions for the event
    permissions = db.query(PermissionModel).filter(
        PermissionModel.event_id == event_id
    ).all()
    
    return permissions

@router.put("/{event_id}/permissions/{user_id}", response_model=Permission)
def update_permission(
    event_id: int,
    user_id: int,
    permission_update: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Check if current user is the owner
    check_event_ownership(db, event_id, current_user.id)
    
    # Find the permission to update
    permission = db.query(PermissionModel).filter(
        PermissionModel.event_id == event_id,
        PermissionModel.user_id == user_id
    ).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    # Don't allow changing owner's role
    if permission.role == RoleEnum.owner.value and permission_update.role != RoleEnum.owner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change the owner's role"
        )
    
    # Update the permission
    permission.role = permission_update.role
    db.commit()
    db.refresh(permission)
    
    return permission

@router.delete("/{event_id}/permissions/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(
    event_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    # Check if current user is the owner
    check_event_ownership(db, event_id, current_user.id)
    
    # Find the permission to delete
    permission = db.query(PermissionModel).filter(
        PermissionModel.event_id == event_id,
        PermissionModel.user_id == user_id
    ).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    # Don't allow removing the owner
    if permission.role == RoleEnum.owner.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the owner's permission"
        )
    
    # Delete the permission
    db.delete(permission)
    db.commit()
    
    return None