"""Authentication API routes for registration and login."""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session
from app.schemas import UserRegister, UserLogin, TokenResponse, UserRead, UserWrapperResponse
from app.services.auth_service import AuthService
from app.core.database import get_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserWrapperResponse, status_code=201)
async def register(
    user_data: UserRegister,
    session: Session = Depends(get_session),
) -> UserWrapperResponse:
    """
    Register a new user.
    
    Args:
        user_data: Registration data (username, email, password, firstname, lastname)
        session: Database session
        
    Returns:
        UserWrapperResponse with user info
        
    Raises:
        HTTPException: If registration fails (duplicate username/email)
    """
    try:
        # Register the user
        user = AuthService.register_user(
            username=user_data.username,
            email=user_data.email,
            firstname=user_data.firstname,
            lastname=user_data.lastname,
            password=user_data.password,
            session=session,
            user_role=user_data.user_role or "user",
        )
        
        # Return response
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    session: Session = Depends(get_session),
) -> TokenResponse:
    """
    Login a user and return JWT token.
    
    Args:
        credentials: Login credentials (username, password)
        session: Database session
        
    Returns:
        TokenResponse with access token and user info
        
    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        user, access_token = AuthService.login_user(
            username=credentials.username,
            password=credentials.password,
            session=session,
        )
        
        # Return response
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserRead(
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
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Login failed")



security = HTTPBearer()

@router.get("/me", response_model=UserWrapperResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> UserWrapperResponse:
    """
    Get current authenticated user info.
    
    Args:
        credentials: Bearer token credentials
        session: Database session
        
    Returns:
        UserWrapperResponse with current user info
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    try:
        from app.core.jwt_utils import decode_token
        
        token = credentials.credentials
        username = decode_token(token)
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = AuthService.get_user_by_username(username, session)
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get user info")
