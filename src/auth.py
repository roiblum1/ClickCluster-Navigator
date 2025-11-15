"""
Authentication module for admin access.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from src.config import config

# HTTP Basic Auth
security = HTTPBasic()


def verify_password(plain_password: str, stored_password: str) -> bool:
    """Verify a password against the stored password."""
    # Simple constant-time comparison
    return secrets.compare_digest(plain_password, stored_password)


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user with username and password."""
    if username != config.admin_username:
        return False
    return verify_password(password, config.admin_password)


async def get_current_admin(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """
    Dependency to verify admin credentials.
    Returns username if authenticated, raises HTTPException otherwise.
    """
    # Use constant-time comparison to prevent timing attacks
    correct_username = secrets.compare_digest(credentials.username, config.admin_username)

    if not correct_username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    if not verify_password(credentials.password, config.admin_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username
