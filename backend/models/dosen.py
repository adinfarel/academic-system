"""
models/dosen.py — Lecturer data

This table stores specific lecturer information.
It is separated from 'users' to avoid interfering with auth and academic data.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean,
    DateTime, ForeignKey, Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database import Base

class Dosen(Base):
    """
    'Lecturer' table — lecturer profile and academic data.

    Relationships:
    - Many-to-one to User
    - One-to-many to Attendance (lecturer who created the attendance session)
    """
    __tablename__ = "dosen"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key to Users
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    
    # Academic Identity
    nidn = Column(String(20), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    study_program = Column(String(100), nullable=False)
    major = Column(String(100), nullable=False)
    positiion = Column(String(100), nullable=True)
    
    # Status
    activate_status = Column(Boolean, default=True)
    
    # Additional Information
    profile_picture = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    # Relationships
    user = relationship("User", back_populates="dosen")
    absensi_sessions = relationship(
        "Absensi",
        back_populates="dosen",
        cascade="all, delete-orphan",
    )
    grade_given = relationship(
        "Grade",
        back_populates="dosen"
    )
    
    def __repr__(self):
        return f"<Dosen nidn={self.nidn} nama={self.full_name}>"