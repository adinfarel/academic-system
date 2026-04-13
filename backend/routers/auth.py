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
    MahasiswaRegisterRequest,
    LecturerRegisterRequest,
    MahasiswaResponse,
)
from backend.services.auth import (
    authenticate_user,
    register_user,
    create_access_token,
    register_dosen,
    register_mahasiswa,
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
    "/register/mahasiswa",
    response_model=MahasiswaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Regiser new student account."
)
def register_mahasiswa_endpoint(
    payload: MahasiswaRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Student registration — one endpoint for users and students.

    No more manual input into the student table.
    Once this endpoint is called, students can log in immediately,
    and all their academic data is properly connected.
    """
    new_user, new_mahasiswa = register_mahasiswa(
        db=db,
        data=payload.model_dump()
    )

    return MahasiswaResponse(
        user_id=new_user.id,
        mahasiswa_id=new_mahasiswa.id,
        username=new_user.username,
        email=new_user.email,
        nim=new_mahasiswa.nim,
        nama_lengkap=new_mahasiswa.full_name,
        role=new_user.role,
    )

@router.post(
    "/register/dosen",
    status_code=status.HTTP_201_CREATED,
    summary="Daftarkan akun dosen baru"
)
def register_dosen_endpoint(
    payload: LecturerRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register lecturer — one endpoint for users and lecturers.
    """
    new_user, new_dosen = register_dosen(
        db=db,
        data=payload.model_dump()
    )

    return {
        "user_id": new_user.id,
        "dosen_id": new_dosen.id,
        "username": new_user.username,
        "email": new_user.email,
        "nidn": new_dosen.nidn,
        "nama_lengkap": new_dosen.full_name,
        "role": new_user.role,
    }

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