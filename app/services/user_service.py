"""User service for managing user data."""
from typing import List, Optional
from sqlmodel import Session, select
from app.models.user import User
from app.schemas import UserUpdate
from app.core.password import hash_password

class UserService:
    """Service for handling user management operations"""
    
    @staticmethod
    def get_all_users(session: Session) -> List[User]:
        """
        Get all users.
        
        Args:
            session: Database session
            
        Returns:
            List of User objects
        """
        return session.exec(select(User)).all()
    
    @staticmethod
    def update_user(user_id: int, user_data: UserUpdate, session: Session) -> Optional[User]:
        """
        Update user details.
        
        Args:
            user_id: ID of user to update
            user_data: Data to update
            session: Database session
            
        Returns:
            Updated User object or None if not found
        """
        user = session.get(User, user_id)
        if not user:
            return None
            
        update_data = user_data.dict(exclude_unset=True)
        
        # Handle password hashing if password is being updated
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = hash_password(update_data.pop("password"))
            
        for key, value in update_data.items():
            setattr(user, key, value)
            
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    
    @staticmethod
    def delete_user(user_id: int, session: Session) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: ID of user to delete
            session: Database session
            
        Returns:
            True if deleted, False if not found
        """
        user = session.get(User, user_id)
        if not user:
            return False
            
        session.delete(user)
        session.commit()
        return True
