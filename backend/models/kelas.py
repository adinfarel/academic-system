"""
models/kelas.py — Class table

Class = the smallest unit of student grouping.
Format: {study_code}-{semester}{letter}
Example: TI-3A, TI-3B, MI-2A

Relationships:
- One-to-many to Students (one class has many students)
- One-to-many to Lecture Schedule (one class has many schedules)
"""

from sqlalchemy import (
    Column, Integer, String,
    DateTime, Boolean, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database import Base

class Kelas(Base):
    """
    'Class' table — master class data per study program per semester.
    """
    __tablename__ = "kelas"
    
    id = Column(Integer, primary_key=True, index=True)
    
    nama = Column(String(20), nullable=False, index=True)
    kode_prodi = Column(String(10), nullable=False)
    
    program_studi = Column(String(100), nullable=False)
    
    semester = Column(Integer, nullable=False)
    
    huruf = Column(String(10), nullable=False)
    tahun_akademik = Column(String(10), nullable=False)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    __table_args__ = (
        UniqueConstraint(
            'kode_prodi', 'semester', 'huruf', 'tahun_akademik',
            name='unique_kelas_per_semester'
        ),
    )
    
    mahasiswa = relationship(
        "Mahasiswa",
        back_populates="kelas"
    )
    jadwal = relationship(
        "JadwalKuliah",
        back_populates="kelas"
    )
    
    def __repr__(self):
        return f"<Kelas {self.nama} ({self.tahun_akademik})>"