"""
models/absensi.py — Recording student attendance

One row = one attendance event:
Student X attended session Y at time Z using facial recognition.
"""

from sqlalchemy import (
    Column, Integer, String, Boolean,
    DateTime, ForeignKey, Text, Float, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from backend.database import Base

class AttendanceStatus(str, enum.Enum):
    """Status of attendance record."""
    HADIR = "hadir"
    TERLAMBAT = "terlambat"
    TIDAK_HADIR = "tidak_hadir"

class AbsensiMethods(str, enum.Enum):
    """Ways attendance was recorded."""
    FACE_RECOGNITION = "face_recognition"
    MANUAL = "manual"

class Absensi(Base):
    """
    'Attendance' table — student attendance log.

    Stores not only attendance/absence status,
    but also facial recognition confidence scores
    for audit trails and CV model debugging.
    """
    __tablename__ = "absensi"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    mahasiswa_id = Column(
        Integer,
        ForeignKey("mahasiswa.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    dosen_id = Column(
        Integer,
        ForeignKey("dosen.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Session Information
    mata_kuliah = Column(String(100), nullable=False)
    kode_mk = Column(String(20), nullable=False)
    ruangan = Column(String(50), nullable=True)
    pertemuan_ke = Column(Integer, nullable=False, default=1)
    
    # Absence Results
    status = Column(
        Enum(AttendanceStatus),
        nullable=False,
        default=AttendanceStatus.TIDAK_HADIR
    )
    method = Column(
        Enum(AbsensiMethods),
        nullable=False,
        default=AbsensiMethods.FACE_RECOGNITION
    )
    
    # FACE RECOGNITION METADATA
    confidence_score = Column(Float, nullable=True)
    
    liveness_score = Column(Float, nullable=True)
    
    is_liveness_passed = Column(Boolean, nullable=True)
    
    # Timestamps
    time_absence = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    mahasiswa = relationship("Mahasiswa", back_populates="absensi")
    dosen = relationship("Dosen", back_populates="absensi_sessions")
    
    def __repr__(self):
        return (
            f"<Absensi mahasiswa_id={self.mahasiswa_id} "
            f"mk={self.mata_kuliah} status={self.status}>"
        )