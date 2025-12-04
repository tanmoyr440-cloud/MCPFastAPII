"""Password hashing utilities using argon2."""
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

# Create argon2 password hasher
hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """
    Hash a password using argon2.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to check against
        
    Returns:
        True if passwords match, False otherwise
    """
    try:
        hasher.verify(hashed_password, plain_password)
        return True
    except (VerifyMismatchError, VerificationError):
        return False
