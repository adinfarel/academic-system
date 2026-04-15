"""
models/user.py — Base model for authentication of all roles

The 'users' table stores login credentials.
Relationship: a user can be a student, lecturer, or admin
(each one in the respective role table).
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from backend.database import Base

# ENUM ROLE
class UserRole(str, enum.Enum):
    """
    Enum = a data type with limited, predefined values.
    Use str to keep the value string in the JSON response.

    Why isn't an enum a regular string?
    → With a regular string, you could type "amdin" and not be noticed.
    → An enum will immediately error if the value is invalid.
    """
    MAHASISWA = "mahasiswa"
    DOSEN = "dosen"
    ADMIN = "admin"
    
# APPROVAL SYSTEM
class RegistrationStatus(str, enum.Enum):
    """
    Status registration account student
    
    PENDING → just registered, awaiting admin review
    APPROVED → approved by admin, code sent to email
    REJECTED → rejected by admin
    ACTIVE → student has logged in for the first time and changed their password
    """
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"

# MODEL
class User(Base):
    """
    'users' table — one row = one login account.

    All roles use this table for authentication.
    Role-specific data (NIM, NIDN, etc.) is contained in the respective table.
    """
    __tablename__ = "users"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Identity
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    
    # Auth
    hashed_password = Column(String(255), nullable=False)
    
    # Role
    role = Column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.MAHASISWA
    )
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Approval
    registration_status = Column(
        Enum(RegistrationStatus),
        nullable=False,
        default=RegistrationStatus.PENDING
    )
    verification_code = Column(
        String(20),
        nullable=True
    )
    verification_code_sent_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    rejection_reason = Column(
        String(500),
        nullable=True
    )
    must_change_password = Column(
        Boolean,
        default=False,
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    mahasiswa = relationship(
        "Mahasiswa",
        back_populates="user",
        uselist=False,
    )
    
    dosen = relationship(
        "Dosen",
        back_populates="user",
        uselist=False,
    )
    
    def __repr__(self):
        """String representation of object — appears during print/debug."""
        return f"<User id={self.id} username={self.username} role={self.role}>"