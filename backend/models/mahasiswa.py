"""
models/mahasiswa.py — Student academic data

This table stores specific student information.
It is separated from 'users' to avoid interfering with auth and academic data.
"""
from sqlalchemy import (
    Column, Integer, String, Boolean,
    DateTime, ForeignKey, LargeBinary, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database import Base

class Mahasiswa(Base):
    """
    'student' table — academic data and face encoding.

    Relationships:
    - Many-to-one to User (each student has one account)
    - One-to-many to Attendance (one student can have many attendance records)
    """
    __tablename__ = "mahasiswa"
    
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
    nim = Column(String(20), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    study_program = Column(String(100), nullable=False)
    major = Column(String(100), nullable=False)
    semester = Column(Integer, nullable=False)
    entry_year = Column(Integer, nullable=False)
    
    # Academic Status
    status_ukt = Column(Boolean, default=False)
    
    # Activate Status
    activate_status = Column(Boolean, default=False)
    
    # Face Recognition
    face_encoding = Column(LargeBinary, nullable=True)
    face_registered_at = Column(DateTime(timezone=True), nullable=True)
    
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
    user = relationship("User", back_populates="mahasiswa")
    absensi = relationship(
        "Absensi",
        back_populates="mahasiswa",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return f"<Mahasiswa nim={self.nim} nama={self.full_name}>"