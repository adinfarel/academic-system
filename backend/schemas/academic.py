"""
schema/academic.py — Request and response schema for academic data

Unlike schema/user.py, which handles authentication,
this file is specifically for CRUD operations on academic data.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MahasiswaUpdateRequest(BaseModel):
    """
    Data that admins can update for a single student.

    Not all fields can be changed — Student ID and user_id
    cannot be changed after they are created because they are the primary identifiers.

    Optional = not all fields are required.
    Admins can update only the UKT_status without having to fill in the other fields (partial update).
    """
    full_name: Optional[str] = None
    study_program: Optional[str] = None
    major: Optional[str] = None
    semester: Optional[int] = None
    entry_year: Optional[int] = None
    status_ukt: Optional[bool] = None
    activate_status: Optional[bool] = None
    notes: Optional[str] = None

class MahasiswaDetailResponse(BaseModel):
    """
    Complete student data response — for both admin and students.
    Does not include face_encoding because it is a large binary file.
    It does not need to be sent to the frontend.
    """
    id: int
    user_id: int
    nim: str
    full_name: str
    study_program: str
    major: str
    semester: int
    entry_year: int
    status_ukt: bool
    activate_status: bool
    face_registered_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    
    email: Optional[str] = None
    username: Optional[str] = None

    class Config:
        from_attributes = True

class MahasiswaSummaryResponse(BaseModel):
    """
    Short student responses — to list all students.
    Fewer fields to avoid overwhelming responses
    if there are many students.
    """
    id: int
    nim: str
    full_name: str
    study_program: str
    semester: int
    status_ukt: bool
    activate_status: bool
    
    class Config:
        from_attributes = True

class LecturerSummaryResponse(BaseModel):
    """Short response lecturer - for list all dosen"""
    id: int
    nidn: str
    full_name: str
    study_program: str
    position: Optional[str] = None
    activate_status: bool
    
    class Config:
        from_attributes = True

class AttendanceRecapResponse(BaseModel):
    """
    Attendance recap for a single course — lecturers only.
    Lecturers can see who attended and how many times.
    """
    kode_mk: str
    mata_kuliah: str
    total_pertemuan: int
    recap: list 
