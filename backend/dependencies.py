"""
dependencies.py — Dependency injection for authentication

This function is injected into the endpoint that requires authentication.
FastAPI automatically executes this function before the endpoint handler is called.

How to use:
    @router.get("/protected")
    def protected_route(current_user: User = Depends(get_current_user)):
        return {"user": current_user.username}
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.auth import decode_access_token, get_user_by_id
from backend.models.user import User, UserRole

# ENDPOINT LOGIN
oauth2_scheme = OAuth2AuthorizationCodeBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Main dependency — extract and verify the user from the JWT token.

    Flow:
    1. OAuth2PasswordBearer extracts the token from the header.
    2. decode_access_token verifies the token is valid and has not expired.
    3. Retrieve the user from the database based on the ID in the token.
    4. Return the user object to the endpoint.

    Args:
        token: JWT token from the Authorization header (auto-inject)
        db: database session (auto-inject)

    Returns:
        User: The currently logged-in user object.

    Raises:
        HTTPException 401: token invalid, expired, or user does not exist.
    """
    payload = decode_access_token(token)
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid"
        )
    
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account de-activate"
        )

    return user

def get_current_activate_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency specific to the admin endpoint.
    Extends from get_current_user — the user must be logged in AND an admin.

    How to use:
        @router.delete("/users/{id}")
        def delete_user(admin: User = Depends(get_current_active_admin)):
            ...
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - Only my Author can access, he is Adin Ramdan Farelino"
        )
    
    return current_user

def get_current_activate_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency specific endpoint for lecturer."""
    if current_user.role not in [UserRole.DOSEN, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - Only Lecturer or Admin"
        )
    
    return current_user

def get_current_active_mahasiswa(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency specific endpoint for student."""
    if current_user.role not in [UserRole.MAHASISWA, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied — only mahasiswa or admin"
        )
        
    return current_user