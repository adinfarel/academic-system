"""
services/auth.py — Authentication and JWT logic

All password hashing and token handling is done here.
The router only calls functions from here — there's no logic in the router.

Principle: Router = thin, Service = fat
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets

from jose import JWSError, jwt
from passlib.context import CryptContext
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.config import get_settings
from backend.models.user import User, UserRole, RegistrationStatus
from backend.services.email import (
    generate_verification_code,
    send_approval_email,
    send_rejection_email,
)
from backend.models.mahasiswa import Mahasiswa
from backend.models.dosen import Dosen
from backend.utils.logger import get_logger

# LOGGER
logger = get_logger(__name__)

# DUMMY PW
# TODO: Yall can replace this Field: Password, cause for production required me as a dev prefer use dummy to prevent subtle bug >.<
dummy_password = secrets.token_urlsafe(16)

# SETTINGS
settings = get_settings()

# PASSWORD HASHING
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain_password: str) -> str:
    """
    Change plain password to be hash bcrypt.
    
    Example:
        hash_password("password123")
        -> "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    
    Args:
        plain_password: real password from user
    
    Returns:
        str: hash bcrypt that safety saved to DB
    """
    return generate_password_hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verification password while login.
    Not decrypt hash - becrypt indeed could not decrypt.
    Which is conducted: re-hash password input, compare its result.
    
    Args:
        plain_password: password that input user while login
        hashed_password: hashed that save at DB
    
    Returns:
        bool: True if match, False if it is not
    """
    return check_password_hash(hashed_password, plain_password)

# JWT

def create_access_token(
    user_id: int,
    username: str,
    role: UserRole,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token containing the user's identity.

    A JWT consists of three parts (separated by dots):
    1. Header: the algorithm used (HS256)
    2. Payload: the stored data (id, role, expiry)
    3. Signature: a hash of the header and payload using SECRET_KEY

    Anyone can read the JWT payload (it's not encrypted, just base64 encoded).
    But it cannot be MODIFIED without SECRET_KEY — because the signature will be invalid.

    Args:
        user_id: user ID from the database
        username: user username
        role: user role (student/lecturer/admin)
        expires_delta: token validity period (default from settings)

    Returns:
        str: JWT token string
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )
    
    # Payload
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role.value,
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    
    # Encode
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    
    return token

def decode_access_token(token: str) -> dict:
    """
    Decode and verify JWT tokens.
    Used in dependency injection to protect endpoints.

    Verification process:
    1. Check signature is valid (unmodified)
    2. Check token is unexpired
    3. Extract payload

    Args:
        token: JWT token string from Authorization header

    Returns:
        dict: payload token (user_id, username, role)

    Raises:
        HTTPException 401: if token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWSError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
            headers={"WWW-Authenticate": "Bearer"}
        )

# DB OPS

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Search for a user in the database by username.
    Also try searching by email if the username isn't found.
    -> This way, the user can log in using either their username or email.

    Args:
        db: Database session from dependency injection
        username: Username or email entered by the user

    Returns:
        User object if found, None if not
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = db.query(User).filter(User.email == username).first()
    
    return user

def get_user_by_id(db: Session, id: int) -> Optional[User]:
    """
    Search for a user in the database by id.
    
    Args:
        db: Database session from dependency injection
        id: User id entered by the user
    
    Returns:
        User object if found, None if not
    """
    return db.query(User).filter(User.id == id).first()

def authenticate_user(
    db: Session,
    username: str,
    password: str,
) -> Optional[User]:
    """
    Verifies the username and password combination.
    Combined with get_user + verify_password.

    Args:
        db: database session
        username: username or email
        password: plain password from user input

    Returns:
        User object if successful, None if failed
    """
    user = get_user_by_username(db, username)
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None # Return none if not matching
    
    if not user.is_active:
        return None # User de-activate
    
    return user

def register_user(
    db: Session,
    email: str,
    username: str,
    password: str,
    role: UserRole = UserRole.MAHASISWA
) -> User:
    """
    Create a new user account in the database.

    Flow:
    1. Check email and username are not already in use
    2. Hash password
    3. Save to database

    Args:
        db: database session
        email: user email
        username: unique username
        password: plain password (will be hashed here)
        role: user role

    Returns:
        Newly created user object
    
    Raises:
        HTTPException 400: kalau email atau username sudah dipakai
    """
    # Check duplicate email
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Check duplicate username
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already used",
        )
    
    new_user = User(
        email=email,
        username=username.lower(),
        hashed_password=hash_password(password),
        role=role,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

def register_mahasiswa(
    db: Session,
    data: dict,
) -> tuple:
    """
    Student registration — fill the users AND student tables in one transaction.
    
    Args:
        db: database session
        data: dict containing all fields from MahasiswaRegisterRequest

    Returns:
        tuple: (User, Student) newly created

    Raises:
        HTTPException 400: if email, username, or student ID number is already in use
    """
    if db.query(User).filter(User.email == data["email"]).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )
    
    if db.query(User).filter(User.username == data["username"]).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already use"
        )

    if db.query(Mahasiswa).filter(Mahasiswa.nim == data["nim"]).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NIM already registered."
        )
    
    try:
        # ADD TABEL USERS
        new_user = User(
            email=data["email"],
            username=data["username"].lower(),
            hashed_password=hash_password(dummy_password),
            role=UserRole.MAHASISWA,
            is_active=False,
            registration_status=RegistrationStatus.PENDING,
        )
        db.add(new_user)
        db.flush()
        
        # ADD TABEL STUDENT
        new_mahasiswa = Mahasiswa(
            user_id=new_user.id,
            nim=data["nim"],
            full_name=data["full_name"],
            study_program=data["study_program"],
            major=data["major"],
            semester=data["semester"],
            entry_year=data["entry_year"]
        )
        db.add(new_mahasiswa)
        
        db.commit()
        db.refresh(new_user)
        db.refresh(new_mahasiswa)
        
        return new_user, new_mahasiswa
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fail create account: {str(e)}"
        )

def approve_mahasiswa(
    db: Session,
    user_id: int
) -> dict:
    """
    Admin approves student registration.

    Flow:
    1. Search for user by ID
    2. Validate the status is still PENDING
    3. Generate an 8-character verification code
    4. Update status → APPROVED, activate account
    5. Send an email containing the code to the student
    6. Return the result

    Why is the code used as a temporary password?
    → Admin does not need to know the student's password
    → Students have full control over their password
    → must_change_password ensures they change it upon first login

    Args:
        db: database session
        user_id: ID of the user to be approved

    Returns:
        dict: approval result + email delivery info
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    
    if user.registration_status != RegistrationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User aldready in status: {user.registration_status}"
        )
    
    code = generate_verification_code() # 8 Random code from technique crypthograph
    
    user.is_active = True
    user.registration_status = RegistrationStatus.APPROVED
    user.verification_code = code
    user.verification_code_sent_at = datetime.now(timezone.utc)
    user.hashed_password = hash_password(code)
    user.must_change_password = True
    
    db.commit()
    
    mahasiswa = user.mahasiswa
    if not mahasiswa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Data student not found."
        )
    mahasiswa.activate_status = True
    
    email_sent = send_approval_email(
        to_email=user.email,
        nama=mahasiswa.full_name,
        nim=mahasiswa.nim,
        verification_code=code
    )
    
    return {
        "message": f"Mahasiswa {mahasiswa.full_name} success approve.",
        "email_sent": email_sent,
        "verification_code": code,
        "user_id": user.id,
    }

def reject_mahasiswa(
    db: Session,
    user_id: int,
    reason: str = None,
):
    """
    The admin rejected the student's registration.

    The user remains in the database with a REJECTED status.
    Why isn't it deleted?
    → Audit trail — the admin can view the registration history
    → If the student complains, there's proof of registration
    → Can be re-approved if the rejection was incorrect

    Args:
        db: database session
        user_id: ID of the rejected user
        reason: Reason for rejection (optional)

    Returns:
        dict: rejection result
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    
    if user.registration_status != RegistrationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User aldready in status: {user.registration_status}"
        )
    
    user.registration_status = RegistrationStatus.REJECTED
    user.is_active = False
    user.rejection_reason = reason
    db.commit()
    
    mahasiswa = user.mahasiswa
    email_sent = False

    if mahasiswa:
        email_sent = send_rejection_email(
            to_email=user.email,
            nama=mahasiswa.full_name,
            reason=reason
        )

    return {
        "message": "Pendaftaran ditolak",
        "email_sent": email_sent,
        "user_id": user.id,
    }

def change_password_first_login(
    db: Session,
    user: User,
    new_password: str
) -> dict:
    """
    Change password on first login after approval.

    Called when must_change_password=True and the student submits a new password.

    Validation:
    - New password must be at least 8 characters
    - New password must not be the same as the old verification code

    Args:
        db: database session
        user: User object currently logged in
        new_password: new password from the student

    Returns:
        dict: confirmation successful
    """
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password at least 8 char."
        )

    # Pastikan password baru berbeda dari kode lama
    if user.verification_code and verify_password(
        new_password, hash_password(user.verification_code)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password dont't same with verification code"
        )

    user.hashed_password = hash_password(new_password)
    user.must_change_password = False
    user.verification_code = None       
    user.verification_code_sent_at = None
    user.registration_status = RegistrationStatus.ACTIVE

    db.commit()

    return {"message": "Password updated successfully. Please log in again."}
    
def register_dosen(
    db: Session,
    data: dict,
) -> tuple:
    """
    Register lecturers — populate the users and lecturers tables in one transaction.
    Same logic as register_mahasiswa.

    Args:
        db: database session
        data: dict containing all fields from the DosenRegisterRequest

    Returns:
        newly created tuple: (User, Lecturer)
    """
    if db.query(User).filter(User.email == data["email"]).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already regist."
        )

    if db.query(User).filter(User.username == data["username"]).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already use"
        )

    if db.query(Dosen).filter(Dosen.nidn == data["nidn"]).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="NIDN already registered."
        )
        
    try:
        new_user = User(
            email=data["email"],
            username=data["username"].lower(),
            hashed_password=hash_password(data["password"]),
            role=UserRole.DOSEN,
        )
        db.add(new_user)
        db.flush()

        new_dosen = Dosen(
            user_id=new_user.id,
            nidn=data["nidn"],
            nama_lengkap=data["nama_lengkap"],
            program_studi=data["program_studi"],
            jurusan=data["jurusan"],
            jabatan=data.get("jabatan"),
        )
        db.add(new_dosen)

        db.commit()
        db.refresh(new_user)
        db.refresh(new_dosen)

        return new_user, new_dosen

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fail create account: {str(e)}"
        )