"""
models/jadwal.py - Class schedule table
"""

from sqlalchemy import (
    Column, Integer, String, Time,
    ForeignKey, Enum, Boolean, DateTime
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from backend.database import Base

class HariKuliah(str, enum.Enum):
    """
    Enum day study
    """
    SENIN = "Senin"
    SELASA = "Selasa"
    RABU = "Rabu"
    KAMIS = "Kamis"
    JUMAT = "Jumat"
    SABTU = "Sabtu"

class JadwalKuliah(Base):
    """
    Table 'jadwal_kuliah' - schedule school routine every week.
    """
    __tablename__ = "jadwal_kuliah"
    
    id = Column(Integer, primary_key=True, index=True)
    
    kode_mk = Column(String(20), nullable=False, index=True)
    nama_mk = Column(String(100), nullable=False)
    sks = Column(Integer, nullable=False)
    
    hari = Column(Enum(HariKuliah), nullable=False, index=True)
    
    jam_mulai = Column(Time, nullable=False)
    jam_selesai = Column(Time, nullable=False)
    ruangan = Column(String(50), nullable=False)
    
    program_studi = Column(String(100), nullable=False)
    semester_ke = Column(Integer, nullable=False)
    
    tahun_akademik = Column(String(10), nullable=False)
    
    dosen_id = Column(
        Integer,
        ForeignKey("dosen.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    dosen = relationship("Dosen", back_populates="jadwal")
    
    def __repr__(self):
        return (
            f"<JadwalKuliah {self.nama_mk} "
            f"{self.hari} {self.jam_mulai}>"
        )