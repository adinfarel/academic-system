"""
models/__init__.py — Register all models with SQLAlchemy

Import all models here so that Base.metadata.create_all()
in main.py can "see" all tables and create them all at once.

Without this, tables won't be created even if the models are defined.
"""

from backend.models.user import User, UserRole
from backend.models.mahasiswa import Mahasiswa
from backend.models.dosen import Dosen
from backend.models.absensi import Absensi, AttendanceStatus, AbsensiMethods

__all__ = [
    "User", "UserRole",
    "Mahsiswa",
    "Dosen",
    "Absensi", "AttendanceStatus", "AbsensiMethods",
]
