"""User management API routes."""
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.schemas import UserRead, UserUpdate, UserWrapperResponse
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.core.database import get_session
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("", response_model=List[UserRead])
async def get_users(
    session: Session = Depends(get_session),
    current_user: UserWrapperResponse = Depends(get_current_user),
) -> List[UserRead]:
    """
    List all users.
    
    Args:
        session: Database session
        current_user: Authenticated user (required)
        
    Returns:
        List of users
    """
    if current_user.user.user_role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    users = UserService.get_all_users(session)
    return [
        UserRead(
            id=user.id,
            username=user.username,
            email=user.email,
            firstname=user.firstname,
            lastname=user.lastname,
            user_role=user.user_role,
            created_at=user.created_at,
            is_active=user.is_active,
            locked=user.locked,
            failed_login_attempts=user.failed_login_attempts
        ) for user in users
    ]

@router.get("/{user_id}", response_model=UserWrapperResponse)
async def get_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: UserWrapperResponse = Depends(get_current_user),
) -> UserWrapperResponse:
    """
    Get user details by ID.
    
    Args:
        user_id: ID of user to retrieve
        session: Database session
        current_user: Authenticated user
        
    Returns:
        User details wrapped in UserWrapperResponse
        
    Raises:
        HTTPException: If user not found
    """
    # Allow users to view their own profile, admins to view any
    if current_user.user.user_role != "admin" and current_user.user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    user = AuthService.get_user_by_id(user_id, session)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user_read = UserRead(
        id=user.id,
        username=user.username,
        email=user.email,
        firstname=user.firstname,
        lastname=user.lastname,
        user_role=user.user_role,
        created_at=user.created_at,
        is_active=user.is_active,
        locked=user.locked,
        failed_login_attempts=user.failed_login_attempts
    )
    return UserWrapperResponse(user=user_read)

@router.put("/{user_id}", response_model=UserWrapperResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    session: Session = Depends(get_session),
    current_user: UserWrapperResponse = Depends(get_current_user),
) -> UserWrapperResponse:
    """
    Update user details.
    
    Args:
        user_id: ID of user to update
        user_data: Data to update
        session: Database session
        current_user: Authenticated user
        
    Returns:
        Updated user details
        
    Raises:
        HTTPException: If user not found
    """
    if current_user.user.user_role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    updated_user = UserService.update_user(user_id, user_data, session)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user_read = UserRead(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        firstname=updated_user.firstname,
        lastname=updated_user.lastname,
        user_role=updated_user.user_role,
        created_at=updated_user.created_at,
        is_active=updated_user.is_active,
        locked=updated_user.locked,
        failed_login_attempts=updated_user.failed_login_attempts
    )
    return UserWrapperResponse(user=user_read)

@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: UserWrapperResponse = Depends(get_current_user),
):
    """
    Delete a user.
    
    Args:
        user_id: ID of user to delete
        session: Database session
        current_user: Authenticated user
        
    Raises:
        HTTPException: If user not found
    """
    if current_user.user.user_role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    success = UserService.delete_user(user_id, session)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return None
