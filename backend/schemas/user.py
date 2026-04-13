"""
schemas/user.py — Validate request and response data for authentication

Pydantic schema = "contract" between client and API.
- Request schema: validate incoming data (from the frontend)
- Response schema: format of outgoing data (to the frontend)

Why separate it from the SQLAlchemy model?
-> Model = database-related
-> Schema = API-related
-> If combined, changes to the database could break the API, and vice versa.
"""

from backend.utils.logger import get_logger

# LOGGER
logger = get_logger(__name__)

from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional
from backend.models.user import UserRole

class UserRegisterRequest(BaseModel):
    """
    Data required to create a new account.
    Pydantic automatically validates the type and format — if the email is invalid,
    it immediately returns a 422 error without us having to manually validate it.
    """
    email: EmailStr
    username: str
    password: str
    role: UserRole = UserRole.MAHASISWA
    
    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        """
        Custom validator — runs automatically when data is entered.
        Ensure the username contains no spaces and is at least 3 characters long.
        """
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        
        if " " in v:
            raise ValueError("Username must not contain spaces")
        
        return v.lower()
    
    @field_validator("password")
    @classmethod
    def password_valid(cls, v: str) -> str:
        """Password must be at least 8 characters."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        return v

class UserLoginRequest(BaseModel):
    """Data login - only username/email and password are required."""
    username: str
    password: str

# Response Schema

class TokenResponse(BaseModel):
    """
    Response after login successful.
    Only send token - Don't ever send password back to client.
    """
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    username: str

class UserResponse(BaseModel):
    """
    Data user safe to send back to frontend.
    Field 'hashed_password' is intentionally excluded for security reasons.
    """
    id: int
    email: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime
    
    class Config:
        """
        from_attributes=True -> allow convertion from SQLAlchemy model.
        Without this, pydantic can not read objects SQLAlchemy immediately.
        """
        from_attributes = True
    
class MahasiswaRegisterRequest(BaseModel):
    """
    Complete data for student account registration.
    """
    email: EmailStr
    username: str
    password: str
    nim: str
    full_name: str
    study_program: str
    major: str
    semester: int = 1
    entry_year: int
    
    @field_validator("username")
    @classmethod
    def username_valid(cls, v: str) -> str:
        """
        Custom validator — runs automatically when data is entered.
        Ensure the username contains no spaces and is at least 3 characters long.
        """
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        
        if " " in v:
            raise ValueError("Username must not contain spaces")
        
        return v.lower()
    
    @field_validator("password")
    @classmethod
    def password_valid(cls, v: str) -> str:
        """Password must be at least 8 characters."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        return v
    
    @field_validator("nim")
    @classmethod
    def nim_valid(cls, v: str) -> str:
        if len(v) < 5:
            raise ValueError("NIM is invalid")
        return v.strip()

class LecturerRegisterRequest(BaseModel):
    """
    Complete data for registering lecturer accounts.
    This single request populates both the user and lecturer tables.
    """
    email: EmailStr
    username: str
    password: str
    nidn: str
    full_name: str
    study_program: str
    major: str
    position: Optional[str] = None

class MahasiswaResponse(BaseModel):
    """Response after student's successful register."""
    user_id: int
    mahasiswa_id: int
    username: str
    email: str
    nim: str
    full_name: str
    role: UserRole

    class Config:
        from_attributes = True