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
    RejectRequest,
    ChangePasswordRequest,
)
from backend.services.auth import (
    authenticate_user,
    register_user,
    create_access_token,
    register_dosen,
    register_mahasiswa,
    approve_mahasiswa,
    reject_mahasiswa,
    change_password_first_login,
)
from backend.models.user import RegistrationStatus
from backend.dependencies import get_current_user, get_current_activate_admin
from backend.models.user import User, UserRole

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
        full_name=new_mahasiswa.full_name,
        role=new_user.role,
    )

@router.post(
    "/register/dosen",
    status_code=status.HTTP_201_CREATED,
    summary="Registered new account lecturer"
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
        "full_name": new_dosen.full_name,
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
        must_change_password=user.must_change_password
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

@router.get(
    "/pending",
    summary="[ADMIN] List all registration that waiting approval."
)
def list_pending_approval(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_activate_admin),
):
    """
    Retrieve all student registrations with PENDING status.
    This is displayed on the admin dashboard for review.
    """
    pending_users = db.query(User).filter(
        User.registration_status == RegistrationStatus.PENDING,
        User.role == UserRole.MAHASISWA,
    ).all()
    
    result = []
    for u in pending_users:
        mhs = u.mahasiswa
        result.append({
            "user_id": u.id,
            "email": u.email,
            "username": u.username,
            "registered_at": u.created_at,
            "mahasiswa": {
                "nim": mhs.nim if mhs else None,
                "full_name": mhs.full_name if mhs else None,
                "study_program": mhs.study_program if mhs else None,
                "major": mhs.major if mhs else None,
                "semester": mhs.semester if mhs else None,
                "entry_year": mhs.entry_year if mhs else None,
            } if mhs else None
        })

    return {
        "total": len(result),
        "pending": result
    }

@router.post(
    "/approve/{user_id}",
    summary="[ADMIN] Approve registration student and sent code to email."
)
def approve_registration(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_activate_admin)
):
    """
    Admin approves registration.
    The system automatically generates a code and sends it to the student's email.
    """
    return approve_mahasiswa(db, user_id)

@router.post(
    "/reject/{user_id}",
    summary="[Admin] Reject registration student"
)
def reject_registration(
    user_id: int,
    payload: RejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_activate_admin)
):
    """
    Admin rejected the registration.
    An automatic rejection email was sent to the student.
    """
    return reject_mahasiswa(db, user_id, payload.reason)

@router.post(
    "/change-password",
    summary="Change password first time after approval."
)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint untuk ganti password saat login pertama.
    Hanya bisa dipanggil kalau must_change_password=True.
    """
    if not current_user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password not have to change"
        )

    return change_password_first_login(db, current_user, payload.new_password)