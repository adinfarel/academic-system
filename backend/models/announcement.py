"""
models/annoucement.py - Table annoucement
"""

from sqlalchemy import (
    Column, Integer, String, Text,
    DateTime, ForeignKey, Enum, Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from backend.database import Base

class AnnouncementTarget(str, enum.Enum):
    """
    Target announcement
    SEMUA = All user that login
    MAHASISWA = Only student
    DOSEN = Only lecturer
    """
    SEMUA = "semua"
    MAHASISWA = "mahasiswa"
    DOSEN = "dosen"
    
class AnnouncementPriority(str, enum.Enum):
    """
    Announcement priority — affects the frontend display.
    INFO = blue, standard
    PENTING = yellow, requires attention
    URGENT = red, must be read
    """
    INFO = "info"
    PENTING = "penting"
    URGENT = "urgent"

class Announcement(Base):
    """
    Table 'announcement' - annoucement academic.
    """
    __tablename__ = "announcement"
    
    id = Column(Integer, primary_key=True, index=True)
    
    judul = Column(String(200), nullable=False)
    konten = Column(Text, nullable=False)
    
    target = Column(
        Enum(AnnouncementTarget),
        nullable=False,
        default=AnnouncementTarget.SEMUA,
    )
    
    priority = Column(
        Enum(AnnouncementPriority),
        nullable=False,
        default=AnnouncementPriority.INFO,
    )
    
    expiry_date = Column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    is_active = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<Announcement judul={self.judul} target={self.target}>"