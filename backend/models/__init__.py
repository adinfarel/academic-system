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
from backend.models.grade import Grade, LetterGrade
from backend.models.jadwal import JadwalKuliah, HariKuliah
from backend.models.announcement import Announcement, AnnouncementTarget
from backend.models.kelas import Kelas

__all__ = [
    "User", "UserRole",
    "Mahasiswa",
    "Dosen",
    "Kelas",
    "Absensi", "AttendanceStatus", "AbsensiMethods",
    "Grade", '"IpsSemester', "LetterGrade",
    "JadwalKuliah", "HariKuliah",
    "Announcement", "AnnouncementTarget"
]
