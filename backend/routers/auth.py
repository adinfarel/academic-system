"""
routers/auth.py — Authentication endpoints

Router = a collection of endpoints that share the same prefix and tag.
All auth endpoints are here: register, login, profile.

Principle: Router as thin as possible — all logic is in services/auth.py
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)
from backend.services.auth import (
    authenticate_user,
    register_user,
    create_access_token,
)
from backend.dependencies import get_current_user
from backend.models.user import User

router = APIRouter()

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new account."
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register new user.
    
    - Email and username must unique
    - Password hash before save
    - Default role: mahasiswa
    """
    new_user = register_user(
        db=db,
        email=payload.email,
        username=payload.username,
        password=payload.password,
        role=payload.role
    )
    return new_user

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and get the JWT Token"
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Log in with your username/email address and password.
    Return a JWT token to be used for subsequent requests.

    The token is sent in the header:
        Authorization: Bearer <token>
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username or password wrong",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = create_access_token(user.id, user.username, user.role)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user.role,
        username=user.username,
    )

@router.get(
    "/me",
    response_model=UserResponse,
    summary="View user profile that is currently login"
)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint protected — requires a valid token in the header.
    Return the profile data of the currently logged in user.

    Test in Swagger: click the 'Authorize' button → enter the token.
    """
    return current_user