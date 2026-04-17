"""
routers/academic.py — Academic data management endpoint

Access per role:
- Admin: can view and edit all data
- Lecturer: can only view their class attendance recap
- Student: can only view their own data

Principle of least privilege:
Each role only has the minimum access it needs.
Lecturers do not need to view data on other students outside their class.
Students do not need to view data on other students.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from backend.database import get_db
from backend.dependencies import (
    get_current_activate_admin,
    get_current_activate_lecturer,
    get_current_active_mahasiswa,
    get_current_user,
)
from backend.models.user import User
from backend.models.mahasiswa import Mahasiswa
from backend.models.dosen import Dosen
from backend.models.absensi import Absensi, AttendanceStatus
from backend.schemas.academic import (
    MahasiswaDetailResponse,
    MahasiswaSummaryResponse,
    MahasiswaUpdateRequest,
    LecturerSummaryResponse,
)

router = APIRouter()

@router.get(
    "/mahasiswa",
    response_model=List[MahasiswaSummaryResponse],
    summary="[ADMIN] List all student's",
)
def list_student(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
):
    """
    Retrieve all student data using pagination.

    skip=0, limit=50 → page 1 (rows 1-50)
    skip=50, limit=50 → page 2 (rows 51-100)
    skip=100, limit=50 → page 3 (rows 101-150)
    """
    mahasiswa = db.query(Mahasiswa).offset(skip).limit(limit).all()
    return mahasiswa

@router.get(
    "/mahasiswa/{nim}",
    response_model=MahasiswaDetailResponse,
    summary="[ADMIN] Detail one student's based on NIM"
)
def get_mahasiswa_detail(
    nim: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_activate_admin),
):
    """
    Retrieve complete data for one student based on their student ID number.
    Including email and username from the users table.
    """
    mahasiswa = db.query(Mahasiswa).filter(
        Mahasiswa.nim == nim
    ).first()
    
    if not mahasiswa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with NIM {nim} not found."
        )
    
    response = MahasiswaDetailResponse(
        id=mahasiswa.id,
        user_id=mahasiswa.user_id,
        nim=mahasiswa.nim,
        full_name=mahasiswa.full_name,
        study_program=mahasiswa.study_program,
        major=mahasiswa.major,
        semester=mahasiswa.semester,
        entry_year=mahasiswa.entry_year,
        status_ukt=mahasiswa.status_ukt,
        activate_status=mahasiswa.activate_status,
        face_registered_at=mahasiswa.face_registered_at,
        notes=mahasiswa.notes,
        created_at=mahasiswa.created_at,
        email=mahasiswa.user.email if mahasiswa.user else None,
        username=mahasiswa.user.username if mahasiswa.user else None,
    )

    return response

@router.put(
    "/mahasiswa/{nim}",
    response_model=MahasiswaDetailResponse,
    summary="[ADMIN] Update data student."
)
def update_mahasiswa(
    nim: str,
    payload: MahasiswaUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_activate_admin),
):
    """
    Update student academic data.

    Use partial updates — only submitted fields are updated.
    Fields that are not submitted remain the same in the database.

    Example: admin only updates status_ukt=true
    → only the status_ukt column changes
    → name, semester, etc. remain the same
    """
    mahasiswa = db.query(Mahasiswa).filter(
        Mahasiswa.nim == nim
    ).first()
    
    if not mahasiswa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with NIM {nim} not found."
        )
    
    update_data = payload.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(mahasiswa, field, value)
    
    db.commit()
    db.refresh(mahasiswa)
    
    return MahasiswaDetailResponse(
        id=mahasiswa.id,
        user_id=mahasiswa.user_id,
        nim=mahasiswa.nim,
        full_name=mahasiswa.full_name,
        study_program=mahasiswa.study_program,
        major=mahasiswa.major,
        semester=mahasiswa.semester,
        entry_year=mahasiswa.entry_year,
        status_ukt=mahasiswa.status_ukt,
        activate_status=mahasiswa.activate_status,
        face_registered_at=mahasiswa.face_registered_at,
        notes=mahasiswa.notes,
        created_at=mahasiswa.created_at,
        email=mahasiswa.user.email if mahasiswa.user else None,
        username=mahasiswa.user.username if mahasiswa.user else None,
    )

@router.delete(
    "/mahasiswa/{nim}",
    summary="[ADMIN] Delete student"
)
def delete_mahasiswa(
    nim: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_activate_admin)
):
    """
    Delete the student from the system.

    Because we're using CASCADE on the foreign key,
    deleting a user → automatically deletes the student and all their attendance records.
    So we're deleting from the users table, not the students table directly.

    In real systems, soft deletes are usually used
    (active_status=False) instead of hard deletes.
    But for this scope, we'll use hard delete first.
    """
    mahasiswa = db.query(Mahasiswa).filter(
        Mahasiswa.nim == nim
    ).first()
    
    if not mahasiswa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with NIM {nim} not found."
        )
    
    user = db.query(User).filter(
        User.id == mahasiswa.user_id
    ).first()
    
    if user:
        db.delete(user)
    
    db.commit()
    
    return {
        "message": f"Student {nim} succesfully deleted from system."
    }

@router.get(
    "/dosen",
    response_model=List[LecturerSummaryResponse],
    summary="[ADMIN] List all lecturer."
)
def list_dosen(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_activate_admin),
    skip: int = 0,
    limit: int = 10,
):
    """Fetch all data lecturer with pagination."""
    lecturers = db.query(Dosen).offset(skip).limit(limit).all()
    return lecturers

@router.get(
    "/me",
    summary="[STUDENT] View data urself."
)
def get_my_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_mahasiswa),
):
    """
    Students can view their own academic data.

    Why is the endpoint separate from /mahawa/{nim}?
    So that students don't need to know their own student ID to access the data.
    Simply log in and automatically get their data from the JWT token.
    """
    mahasiswa = db.query(Mahasiswa).filter(
        Mahasiswa.user_id == current_user.id
    ).first()
    
    if not mahasiswa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student data not found. Call admin."
        )
    
    total_hadir = db.query(Absensi).filter(
        Absensi.mahasiswa_id == mahasiswa.id,
        Absensi.status == AttendanceStatus.HADIR
    ).count()
    
    mk_list = db.query(Absensi.mata_kuliah, Absensi.kode_mk).filter(
        Absensi.mahasiswa_id == mahasiswa.id
    ).distinct().all()
    
    return {
        "profile": {
            "nim": mahasiswa.nim,
            "full_name": mahasiswa.full_name,
            "study_program": mahasiswa.study_program,
            "major": mahasiswa.major,
            "semester": mahasiswa.semester,
            "entry_year": mahasiswa.entry_year,
            "activate_status": mahasiswa.activate_status,
        },
        "academic": {
            "status_ukt": (
                "Lunas" if mahasiswa.status_ukt else "Belum Lunas"
            ),
            "total_kehadiran": total_hadir,
            "mata_kuliah_diikuti": [
                {"nama": mk.mata_kuliah, "kode": mk.kode_mk}
                for mk in mk_list
            ],
            "face_registered": mahasiswa.face_registered_at is not None,
        }
    }

@router.get(
    "/kelas/{kode_mk}",
    summary="[LECTURER] Recap attendance per subject."
)
def get_recap_class(
    kode_mk: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_activate_lecturer),
):
    """
    Lecturers view attendance summaries for specific courses.

    Displays:
    - Total number of meetings that have taken place
    - Per student: number of total meetings attended
    - Percentage of attendance per student
    """
    records = db.query(Absensi).filter(
        Absensi.kode_mk == kode_mk,
    ).all()
    
    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"There's no absence data for subject {kode_mk}"
        )
    
    total_pertemuan = db.query(
        func.max(Absensi.pertemuan_ke)
    ).filter(
        Absensi.kode_mk == kode_mk
    ).scalar() or 0
    
    nama_mk = records[0].mata_kuliah
    
    kehadiran_map = {}
    for record in records:
        mhs_id = record.mahasiswa_id
        if mhs_id not in kehadiran_map:
            kehadiran_map[mhs_id] = {
                "mahasiswa_id": mhs_id,
                "total_attendance": 0
            }
        
        if record.status == AttendanceStatus.HADIR:
            kehadiran_map[mhs_id]["total_attendance"] += 1
    
    recap = []
    for mhs_id, data in kehadiran_map.items():
        mahasiswa = db.query(Mahasiswa).filter(
            Mahasiswa.id == mhs_id,
        ).first()
        
        if mahasiswa:
            total_attendance = data["total_attendance"]
            persentase = (
                round((total_attendance / total_pertemuan) * 100, 1)
                if total_pertemuan > 0 else 0
            )

            recap.append(
                {
                    "nim": mahasiswa.nim,
                    "nama": mahasiswa.full_name,
                    "jumlah_hadir": total_attendance,
                    "total_pertemuan": total_pertemuan,
                    "persentase_kehadiran": f"{persentase}%",
                    "status_kehadiran": (
                        "Aman" if persentase >= 75 else "Perlu Perhatian"
                    ),
                }
            )
    
    recap.sort(key=lambda x: x["total_attendance"], reverse=True)
    
    return {
        "kode_mk": kode_mk,
        "mata_kuliah": nama_mk,
        "total_pertemuan": total_pertemuan,
        "total_mahasiswa": len(recap),
        "rekap": recap,
    }