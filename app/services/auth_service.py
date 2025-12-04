"""Authentication service for user registration and login."""
from datetime import datetime, timezone
from sqlmodel import Session, select
from app.models.user import User
from app.core.password import hash_password, verify_password
from app.core.jwt_utils import create_access_token


class AuthService:
    """Service for handling user authentication"""
    
    @staticmethod
    def register_user(username: str, email: str, firstname: str, lastname: str, password: str, session: Session, user_role: str = "user") -> User:
        """
        Register a new user.
        
        Args:
            username: Username for new user
            email: Email for new user
            firstname: First name
            lastname: Last name
            password: Plain text password
            session: Database session
            user_role: Role of the user (default: "user")
            
        Returns:
            Created User object
            
        Raises:
            ValueError: If username or email already exists
        """
        # Check if username exists
        existing_user = session.exec(
            select(User).where(User.username == username)
        ).first()
        if existing_user:
            raise ValueError(f"Username '{username}' already exists")
        
        # Check if email exists
        existing_email = session.exec(
            select(User).where(User.email == email)
        ).first()
        if existing_email:
            raise ValueError(f"Email '{email}' already registered")
        
        # Create new user
        user = User(
            username=username,
            email=email,
            firstname=firstname,
            lastname=lastname,
            hashed_password=hash_password(password),
            created_at=datetime.now(timezone.utc).isoformat(),
            is_active=True,
            user_role=user_role,
            locked=False,
            failed_login_attempts=0
        )
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return user
    
    @staticmethod
    def login_user(username: str, password: str, session: Session) -> tuple[User, str]:
        """
        Authenticate a user and return JWT token.
        
        Args:
            username: Username to authenticate
            password: Plain text password
            session: Database session
            
        Returns:
            Tuple of (User object, JWT token string)
            
        Raises:
            ValueError: If user not found or password incorrect
        """
        # Find user by username
        user = session.exec(
            select(User).where(User.username == username)
        ).first()
        
        if not user:
            raise ValueError("Invalid username or password")
            
        # Check if account is locked
        if user.locked:
            raise ValueError("Account locked due to too many failed attempts")
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            # Increment failed attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked = True
            session.add(user)
            session.commit()
            raise ValueError("Invalid username or password")
        
        # Reset failed attempts on successful login
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            session.add(user)
            session.commit()
        
        # Check if user is active
        if not user.is_active:
            raise ValueError("User account is disabled")
        
        # Create JWT token
        access_token = create_access_token(data={"sub": user.username})
        
        return user, access_token
    
    @staticmethod
    def get_user_by_username(username: str, session: Session) -> User:
        """
        Get user by username.
        
        Args:
            username: Username to look up
            session: Database session
            
        Returns:
            User object or None if not found
        """
        return session.exec(
            select(User).where(User.username == username)
        ).first()
    
    @staticmethod
    def get_user_by_id(user_id: int, session: Session) -> User:
        """
        Get user by ID.
        
        Args:
            user_id: User ID to look up
            session: Database session
            
        Returns:
            User object or None if not found
        """
        return session.exec(
            select(User).where(User.id == user_id)
        ).first()
